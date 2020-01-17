import { configureStore, combineReducers } from "@reduxjs/toolkit"
import LocalizedStrings from "react-localization"
import { Appearance } from "./appearance"
import { env } from "process"

function initializeStore() {
    // Only page-critical reducers go here.
    const reducers = {
        appearance: Appearance.reducer, 
    }

    const store = configureStore({
        reducer: reducers
    })

    // Pretty much straight out of Redux docs.
    store.asyncReducers = {}
    store.injectReducers = (asyncReducers) => {
        Object.assign(store.asyncReducers, asyncReducers)
        store.replaceReducer(combineReducers({...store.asyncReducers, ...reducers}))
    }

    return store
}

const store = window._infraStore? window._infraStore : initializeStore()
const strings = window._infraStrings? window._infraStrings : new LocalizedStrings({dummy: {}})
window._infraStore = store
window._infraStrings = strings

function getDocumentLocale() {
    const lang = document.querySelector("html").lang
    if (!lang) {
        console.warn("Pages using Infra should have a html lang attribute. Defaulting to en.")
        return "en" 
    }
    return lang
}

function enableStateWriteback() {
    window._infraWritebackEnabled = true
    console.debug("State writeback is now enabled!")
}

function canWritebackState() {
    return window._infraWritebackEnabled
}

async function initialize() {
    const locale = getDocumentLocale()
    const stringsMod = await import(`./lang/${locale}.js`)

    strings.setContent({
        locale: stringsMod.default,
    })
    strings.setLanguage(locale)
}

function isDevelopmentEnv() {
    return env.NODE_ENV === "development"
}

export default {
    initialize,
    store,
    strings,
    canWritebackState,
    enableStateWriteback,
    isDevelopmentEnv,
    getDocumentLocale,
}
