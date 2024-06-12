from datetime import time
from random import choice

import extra_streamlit_components as stx
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from punctual.new_core import Schedule
from punctual.new_core import punctual


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


@st.cache_resource(experimental_allow_widgets=True)
def get_manager():
    return stx.CookieManager()


cookie_manager = get_manager()

_ENTRIES_COOKIE_NAME = 'punctual_entries'
_ENTRIES_COOKIE_SEPARATOR = '%'

# STREAMLIT

# authentication
with open('./auth/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

authenticator.login()

# init state
if 'entries' not in st.session_state:
    cookie: str | None = cookie_manager.get(_ENTRIES_COOKIE_NAME)
    if cookie != '' and cookie is not None:
        st.session_state.entries = cookie.split(_ENTRIES_COOKIE_SEPARATOR)
    else:
        st.session_state.entries = []

if 'random_placeholder' not in st.session_state:
    st.session_state.random_placeholder = random_placeholder()


def main():
    with st.form('entry_form'):
        entry_name = st.text_input('Activity',
                                   value=None,
                                   placeholder=st.session_state.random_placeholder,
                                   help='Specify the duration of the activity you want to schedule')
        entry_start_time = st.time_input("Start time",
                                         value=None,
                                         help='Indicate the mandatory start time of the activity, if applicable')
        entry_col, reset_col = st.columns(2)
        with entry_col:
            entry_form_submit = st.form_submit_button('Schedule', use_container_width=True)
        with reset_col:
            reset_form_submit = st.form_submit_button('Reset', use_container_width=True)

    if entry_form_submit:
        if entry_name is None:
            st.warning('Please enter a value to enable scheduling')
        elif entry_start_time:
            st.session_state.entries.append(f'{entry_name}; {to_hour(entry_start_time)}')
        else:
            st.session_state.entries.append(f'{entry_name}')

    if reset_form_submit:
        st.session_state.entries = []

    with st.empty():
        if len(st.session_state.entries) > 0:
            st.write(streamlit_punctual())


# authentication deep dive:
# https://pypi.org/project/streamlit-authenticator/
if st.session_state["authentication_status"]:
    main()
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

# update cookies
cookie_manager.set(cookie=_ENTRIES_COOKIE_NAME,
                   val=_ENTRIES_COOKIE_SEPARATOR.join(st.session_state.entries))
