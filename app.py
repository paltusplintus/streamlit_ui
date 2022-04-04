import json
import streamlit as st
from neointerface import NeoInterface
from pathlib import Path

APP = "my_app1"
APP_JSON = Path("data") / Path("graph-driven-app-metadata.json")

neo = NeoInterface()
neo.clean_slate()
f = open(APP_JSON, "r")
neo.load_arrows_dict(json.load(f))

if 'active_screen' not in st.session_state:
    st.session_state.active_screen = 0

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

app_params = {}
screen = st.empty()

def process_query(meta:dict):
    if meta.get("type") == "query":
        q = meta.get("query")
        if meta.get("params"):
            params = json.loads(meta.get("params"))
        else:
            params = {}
        params = {**params,
                  **{id: widget for id, widget in app_params.items()}}
        return neo.query(q, params)

def render(ord: int):
    for i, app_meta_item in enumerate(app_meta):
        if i == ord:
            screen_meta = fetch_metadata(neo, "Screen", {"node_id": app_meta_item['node_id']})
            with screen.container():
                for j, widget_meta in enumerate(screen_meta):
                    if widget_meta.get("type") == "Text":
                        widget = st.write(widget_meta.get("label"), key=(i * 1000 + j))
                    elif widget_meta.get("type") == "Input":
                        widget = st.text_input(label="", value="", help=None, key=(i * 1000 + j))
                    elif widget_meta.get("type") == "Button":
                        widget = st.button(label=widget_meta.get("label"), key=(i * 1000 + j))
                        actions = fetch_metadata(neo, "Widget", {"node_id": widget_meta['node_id']})
                        if widget:
                            for action in actions:
                                res = process_query(action)
                                if action.get("type") == "next screen":
                                    st.session_state.active_screen += 1
                                    render(st.session_state.active_screen)
                    if widget_meta.get("id"):
                        app_params[widget_meta.get("id")] = widget
                break
        else:
            screen.empty()


render(st.session_state.active_screen)