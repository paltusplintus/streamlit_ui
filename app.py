import streamlit as st
from neointerface import NeoInterface
from screen import Screen

neo = NeoInterface()
s = Screen(interface = neo, node_id = 1)