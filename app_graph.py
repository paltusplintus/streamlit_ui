import json
import re
import streamlit as st
from neointerface import NeoInterface
from pathlib import Path

APP = "my_app1"
APP_JSON = Path("data") / Path("graph-driven-app-metadata.json")

neo = NeoInterface()
neo.clean_slate()
f = open(APP_JSON, "r")
neo.load_arrows_dict(json.load(f))

class App:
    def __init__(self, interface: NeoInterface):
        self.interface = interface
        self.app_meta = self.fetch_metadata("App", {"id": APP})
        self.app_params = {}
        self.screen = st.empty()
        self.render(0)

    def fetch_metadata(self, label: str, where: dict = None):
        if not where:
            where = {}
        q = f"""
        MATCH path=(s:`{label}`)-[r]->()-[:NEXT*0..100]->(z)
        WHERE NOT r:NEXT AND apoc.map.submap(apoc.map.merge(s, {{node_id: id(s)}}), keys($where)) = $where AND NOT (z)-[:NEXT]->()
        WITH nodes(path)[1..] as coll
        UNWIND coll as item
        RETURN apoc.map.merge (item, {{node_id: id(item)}}) as item
        """
        params = {"where": where}
        items = [res['item'] for res in self.interface.query(q, params)]
        return items

    def process_query(self, meta: dict):
        if meta.get("query"):
            q = meta.get("query")
            if meta.get("params"):
                params = json.loads(meta.get("params"))
            else:
                params = {}
            params = {**params,
                      **{id: widget for id, widget in self.app_params.items()}}
            res = neo.query(q, params)
            if res:
                self.app_params = {**self.app_params, **res[-1]} # only last reslut of the query is written into params
            return res

    def process_param_str(self, s:str):
        mod_s = s
        for param in re.findall(r'\$(\w+?)\b', s):
            if param in self.app_params.keys():
                mod_s = mod_s.replace(f"${param}", self.app_params[param])
        return mod_s

    def render(self, ord: int):
        for i, app_meta_item in enumerate(self.app_meta):
            if i == ord:
                screen_meta = self.fetch_metadata("Screen", {"node_id": app_meta_item['node_id']})
                with self.screen.container():
                    for j, widget_meta in enumerate(screen_meta):
                        if widget_meta.get("type") == "Text":
                            self.process_query(widget_meta)
                            widget = st.write(self.process_param_str(widget_meta.get("label")))
                        elif widget_meta.get("type") == "Input":
                            widget = st.text_input(label="", value="", help=None)
                        elif widget_meta.get("type") == "Button":
                            widget = st.button(label=widget_meta.get("label"))
                            actions = self.fetch_metadata("Widget", {"node_id": widget_meta['node_id']})
                            if widget:
                                for action in actions:
                                    res = self.process_query(action)
                                    if action.get("type") == "next screen":
                                        st.session_state.active_screen += 1
                                        self.render(st.session_state.active_screen)
                        if widget_meta.get("id"):
                            self.app_params[widget_meta.get("id")] = widget
                    break
            else:
                self.screen.empty()


if 'active_screen' not in st.session_state:
    st.session_state.active_screen = 0
app = App(interface=neo)
