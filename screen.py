import streamlit as st
import json
from neointerface import NeoInterface


class Screen:
    def __init__(self, interface: NeoInterface, node_id: int):
        self.interface = interface
        self.node_id = node_id
        self.widgets = []
        self.placeholders = []
        self.params = None
        for i in range(30):
            self.placeholders.append(st.empty)
        self.fetch_metadata()
        self.display()

    @property
    def widgets_dict(self):
        return {widget.get("id"): self.placeholders[i] for i, widget in enumerate(self.widgets) if widget.get("id")}

    def get(self, id):
        for widget in self.widgets:
            if widget.get("id") == id:
                return widget
        return None

    def fetch_metadata(self):
        q = """
        MATCH path=(s:Screen)-[:START]->()-[:NEXT*0..100]->(z)
        WHERE id(s) = $node_id AND NOT (z)-[:NEXT]->()
        WITH nodes(path)[1..] as coll
        UNWIND coll as widget
        RETURN apoc.map.merge (widget, {node_id: id(widget)}) as widget
        """
        params = {"node_id": self.node_id}
        self.widgets = [res['widget'] for res in self.interface.query(q, params)]
        print(self.widgets)

    def display(self):
        for i, widget in enumerate(self.widgets):
            if widget.get("type") == "Text":
                self.placeholders[i] = Text(widget)
            elif widget.get("type") == "Input":
                self.placeholders[i] = Input(widget)
            elif widget.get("type") == "Button":
                self.placeholders[i] = Button(parent=self, interface=self.interface, meta=widget)


class Widget:
    def __init__(self, meta):
        self.meta = meta


class Text(Widget):
    def __init__(self, *args, **kwargs):
        super(Text, self).__init__(*args, **kwargs)
        self.widget = st.write(self.meta.get("label"))
        self.widget


class Input(Widget):
    def __init__(self, *args, **kwargs):
        super(Input, self).__init__(*args, **kwargs)
        self.widget = st.text_input(label="", value="", help=None)
        self.widget


class Button(Widget):
    def __init__(self, parent: Screen, interface: NeoInterface, *args, **kwargs):
        super(Button, self).__init__(*args, **kwargs)
        self.parent = parent
        self.interface = interface
        self.actions = []
        self.fetch_actions()
        print(self.meta.get("node_id"))
        print(self.actions)
        self.widget = st.button(label=self.meta.get("label"), on_click=self.on_click, args=(self.actions, ))
        self.widget

    def on_click(self, actions):
        for action in self.actions:
            if action.get("type") == "query":
                q = action.get("query")
                if action.get("params"):
                    params = json.loads(action.get("params"))
                else:
                    params = {}
                params = {**params, **{id: widget_class.widget for id, widget_class in self.parent.widgets_dict.items()}}
                self.parent.placeholders[5] = st.write(str((q) + str(params)))
                res = self.interface.query(q, params)
                self.parent.placeholders[6] = st.write(str(res))
            elif action.get("type") == "next screen":
                pass

    def fetch_actions(self):
        q = """
        MATCH path=(w:Widget)-[:ACTION]->()-[:NEXT*0..100]->(z)
        WHERE id(w) = $node_id AND NOT (z)-[:NEXT]->()
        WITH nodes(path)[1..] as coll
        UNWIND coll as action
        RETURN action
        """
        params = {"node_id": self.meta.get("node_id")}
        self.actions = [res['action'] for res in self.interface.query(q, params)]
