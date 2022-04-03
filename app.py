import json
import streamlit as st
from neointerface import NeoInterface

neo = NeoInterface()

APP = "my_app1"
if 'active_screen' not in st.session_state:
    st.session_state.active_screen = 0

st.write(st.session_state.active_screen)

def fetch_metadata(interface: NeoInterface, label: str, where: dict = None):
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
    items = [res['item'] for res in interface.query(q, params)]
    return items


app_meta = fetch_metadata(neo, "App", {"id": APP})

for i, screen in enumerate(app_meta):
    if i == st.session_state.active_screen:
        screen_meta = fetch_metadata(neo, "Screen", {"node_id": screen['node_id']})
        screen_dct = {}
        widgets_dict_by_id = {}
        actions_dct = {}
        for j, widget_meta in enumerate(screen_meta):
            if widget_meta.get("type") == "Text":
                screen_dct[j] = st.write(widget_meta.get("label"))
                if widget_meta.get("id"):
                    widgets_dict_by_id[widget_meta.get("id")] = screen_dct[j]
            elif widget_meta.get("type") == "Input":
                screen_dct[j] = st.text_input(label="", value="", help=None)
                if widget_meta.get("id"):
                    widgets_dict_by_id[widget_meta.get("id")] = screen_dct[j]
            elif widget_meta.get("type") == "Button":
                screen_dct[j] = st.button(label=widget_meta.get("label"))
                if widget_meta.get("id"):
                    widgets_dict_by_id[widget_meta.get("id")] = screen_dct[j]
                actions_dct[j] = fetch_metadata(neo, "Widget", {"node_id": widget_meta['node_id']})
                if screen_dct[j]:
                    for action in actions_dct[j]:
                        if action.get("type") == "query":
                            q = action.get("query")
                            if action.get("params"):
                                params = json.loads(action.get("params"))
                            else:
                                params = {}
                            params = {**params,
                                      **{id: widget for id, widget in widgets_dict_by_id.items()}}
                            res = neo.query(q, params)
                        elif action.get("type") == "next screen":
                            st.session_state.active_screen += 1