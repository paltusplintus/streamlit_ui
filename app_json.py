import json
import jsonlines
import re
import time
from datetime import datetime
import streamlit as st
from pathlib import Path

APP = "my_app1"
APP_JSON = Path("data") / Path("json-driven-app-metadata.json")


class App:
    def __init__(self, metadata_path: Path,
                 save_path: str = Path("mnt") / Path("artifacts") / Path("streamlit_app")):
        self.metadata_path = metadata_path
        self.save_path = save_path
        self.save_path.mkdir(parents=True, exist_ok=True)
        f = open(APP_JSON, "r")
        self.app_meta = json.load(f)
        self.app_params = {}
        self.screen = st.empty()
        self.render(0)

    def process_param_str(self, s: str):
        mod_s = s
        for param in re.findall(r'\$(\w+?)\b', s):
            if param in self.app_params.keys():
                mod_s = mod_s.replace(f"${param}", self.app_params[param])
        return mod_s

    def render(self, ord: int):
        for i, screen_meta in enumerate(self.app_meta["Screen"]):
            if i == ord:
                with self.screen.container():
                    for j, widget_meta in enumerate(screen_meta["Widget"]):
                        if widget_meta.get("type") == "Text":
                            widget = st.write(self.process_param_str(widget_meta.get("label")))
                        elif widget_meta.get("type") == "Input":
                            widget = st.text_input(label="", value="", help=None)
                        elif widget_meta.get("type") == "Button":
                            widget = st.button(label=widget_meta.get("label"))
                            actions = widget_meta.get("Action")
                            if widget:
                                for action in actions:
                                    if action.get("set_param"):
                                        set_param = action.get("set_param")
                                        for key, item in set_param.items():
                                            self.app_params[key] = self.process_param_str(item)
                                    if action.get("type") == "save_params":
                                        k = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                                        if action.get("save_params"):
                                            save = {k: {param: self.app_params[param]} for param in
                                                    action.get("save_params")}
                                        else:
                                            save = {k: self.app_params}
                                        with jsonlines.open(self.save_path / Path(
                                                self.app_meta.get("id") + ".jsonl"), "a") as writer:  # for writing
                                            writer.write(save)
                                    if action.get("type") == "next screen":
                                        st.session_state.active_screen += 1
                                        self.render(st.session_state.active_screen)
                        if widget_meta.get("id"):
                            self.app_params[widget_meta.get("id")] = widget
                break
            else:
                self.screen.empty()
                time.sleep(0.1)  # otherwise the self.screen does not get cleaned-up


if 'active_screen' not in st.session_state:
    st.session_state.active_screen = 0
app = App(APP_JSON)
