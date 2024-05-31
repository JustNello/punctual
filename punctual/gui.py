from datetime import time
from random import choice

import streamlit as st

from punctual.new_core import Schedule
from punctual.new_core import punctual


# TODO continue from these:
# https://docs.streamlit.io/develop/concepts/architecture/forms
# https://docs.streamlit.io/develop/api-reference
# https://docs.streamlit.io/develop/api-reference/execution-flow/st.form_submit_button


# UTILIT METHODS


def random_placeholder() -> str:
    opts = [
        '2h33m',
        '1h',
        '45m',
        'Colosseo, Roma, Italia -> Piazza della Repubblica 00185, Roma RM',
        'Eating pizza'
    ]
    return choice(opts)


def to_hour(user_time: time) -> str:
    return user_time.strftime('%H:%M')


def streamlit_punctual() -> Schedule:
    return punctual(
        entries=st.session_state.entries,
        usr_synonyms=[],
        online=True,
        contingency_in_minutes=2
    )


# STREAMLIT


if 'entries' not in st.session_state:
    st.session_state.entries = []


if 'random_placeholder' not in st.session_state:
    st.session_state.random_placeholder = random_placeholder()


with st.form('entry_form'):
    entry_name = st.text_input('Activity',
                               value=None,
                               placeholder=st.session_state.random_placeholder,
                               help='Specify the duration of the activity you want to schedule')
    entry_start_time = st.time_input("Start time",
                                     value=None,
                                     help='Indicate the mandatory start time of the activity, if applicable')
    entry_form_submit = st.form_submit_button('Schedule', use_container_width=True)


if entry_form_submit:
    if entry_name is None:
        st.warning('Please enter a value to enable scheduling')
    elif entry_start_time:
        st.session_state.entries.append(f'{entry_name}; {to_hour(entry_start_time)}')
    else:
        st.session_state.entries.append(f'{entry_name}')


with st.empty():
    if len(st.session_state.entries) > 0:
        st.write(streamlit_punctual())
