import { createSlice } from "@reduxjs/toolkit"
import Cookies from "js-cookie"
import React from "react"
import Infra from "./infra"
import { connect } from "react-redux"
import { MultiValueSwitch } from "./ui_lib"
import { requestStoragePermission } from "./storage_permission"

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
            Cookies.set("nfm", state.filterMode, {
                expires: 1333337
            })
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

class _NewsFilterSwitchInternal extends MultiValueSwitch {
    getChoices() {
        return [FilterMode.anything, FilterMode.gachaAndEventsOnly]
    }
    
    getLabelForChoice(v) {
        switch(v) {
        case FilterMode.anything:
            return Infra.strings.NewsFilter.Option.No
        case FilterMode.gachaAndEventsOnly:
            return Infra.strings.NewsFilter.Option.Yes
        }
    }
    
    getCurrentSelection() {
        return this.props.filterMode
    }
    
    changeValue(toValue) {
        const nextVal = parseInt(toValue)
        requestStoragePermission().then((canProceed) => {
            if (canProceed)
                this.props.setMode(nextVal)
        })
    }

    animationDidFinish() {
        window.location.reload()
    }
}

const NewsFilterSwitchInternal = connect((state) => { return state.newsFilter },
    (dispatch) => {
        return {
            setMode: (m) => dispatch({type: `${NewsFilter.actions.setMode}`, mode: m})
        }
    })(_NewsFilterSwitchInternal)

export function NewsFilterSwitch() {
    return <div className="kars-sub-navbar is-right">
        <span className="item">{Infra.strings.NewsFilter.Title}</span>
        <NewsFilterSwitchInternal />
    </div>
}

export function initWithRedux(store) {
    store.dispatch({type: `${NewsFilter.actions.loadFromCookie}`})
}