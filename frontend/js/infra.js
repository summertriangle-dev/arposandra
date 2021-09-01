import { configureStore, combineReducers } from "@reduxjs/toolkit"
import LocalizedStrings from "localized-strings"
import { Appearance } from "./appearance"

function initializeShared(name, newFunc) {
    if (window[name] === undefined) {
        window[name] = newFunc()
    }

    return window[name]
}

const store = (() => {
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
})()

const strings = new LocalizedStrings({dummy: {}})

const componentRegistry = {}

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

function registerComponent(name, aClass) {
    componentRegistry[name] = aClass
}

function registerComponents(cMap) {
    Object.assign(componentRegistry, cMap)
}

export default {
    initialize,
    store,
    strings,
    componentRegistry,
    registerComponent,
    registerComponents,
    canWritebackState,
    enableStateWriteback,
    getDocumentLocale,
}
