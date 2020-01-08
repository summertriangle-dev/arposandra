import { createSlice } from "@reduxjs/toolkit"
import Cookies from "js-cookie"
import React from "react"
import Infra from "./infra"
import { connect } from "react-redux"

const FilterMode = Object.freeze({
    anything: 0,
    gachaAndEventsOnly: 1
})

export const NewsFilter = createSlice({
    name: "newsFilter",
    initialState: {
        filterMode: FilterMode.anything,
    },
    reducers: {
        setMode: (state, action) => {
            state.filterMode = action.mode
            Cookies.set("nfm", state.filterMode)
            setTimeout(() => window.location.reload(), 16)
        },
        loadFromCookie: (state) => {
            const p = parseInt(Cookies.get("nfm"))
            if (isNaN(p)) {
                state.filterMode = FilterMode.anything
            } else {
                state.filterMode = p
            }
        }
    }
})

class _NewsFilterSwitch extends React.Component {
    isSelected(m) {
        return this.props.filterMode === m? "selected" : null
    }

    render() {
        return <div className="kars-sub-navbar is-left">
            <span className="item">{Infra.strings["NFS.Title"]}</span>
            <div className="item kars-image-switch always-active">
                <a className={this.isSelected(FilterMode.anything)} 
                    onClick={() => this.props.setMode(FilterMode.anything)}>
                    {Infra.strings["NFSOption.No"]}
                </a>
                <a className={this.isSelected(FilterMode.gachaAndEventsOnly)} 
                    onClick={() => this.props.setMode(FilterMode.gachaAndEventsOnly)}>
                    {Infra.strings["NFSOption.Yes"]}
                </a>
            </div>
        </div>
    }
}

export const NewsFilterSwitch = connect((state) => { return state.newsFilter },
    (dispatch) => {
        return {
            setMode: (m) => dispatch({type: `${NewsFilter.actions.setMode}`, mode: m})
        }
    })(_NewsFilterSwitch)

export function initWithRedux(store) {
    store.dispatch({type: `${NewsFilter.actions.loadFromCookie}`})
}