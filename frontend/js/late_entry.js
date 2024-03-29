import React from "react"
import ReactDOM from "react-dom"
import {Provider} from "react-redux"

import Infra from "./infra"
// This will automatically patch Infra.strings to support JSX placeholders. Neat!
import "react-localization"
import * as TLInject from "./tlinject"
import * as Album from "./album"
import * as Experiments from "./experiments"
import { Appearance } from "./appearance"
import { CardDisplayModeSwitcher, ImageSwitcher, SkillTreeLoader } from "./card_page_components"
import { initLangMenu } from "./lang_menu"
import { hasStoragePermission, requestStoragePermission } from "./storage_permission"
import * as GutterMenu from "./gutter"
import * as NavMenu from "./nav_menu"
import { MemberListDisplaySwitcher } from "./member_list"

const FLG_CS_SHOW_DEV_INFO_E = 0x2

async function initializeContextDependentModules() {
    if (!document.body.dataset.inject) {
        return
    }

    const wantModules = document.body.dataset.inject.split(/ /g)
    if (wantModules.indexOf("card") != -1) {
        Album.injectIntoPage()
    }
    if (wantModules.indexOf("saint") != -1) {
        import("./event-tracker/event_tracker").then((EventTracker) => EventTracker.injectIntoPage())
    }
    if (wantModules.indexOf("experiments") != -1) {
        Experiments.injectIntoPage()
    }
    if (wantModules.indexOf("transcript") != -1) {
        const mod = await import("./transcript/transcript")
        Infra.registerComponent("StoryViewer", mod.StoryViewer)
    }
    if (wantModules.indexOf("search") != -1) {
        const mod = await import("./search/search")
        mod.initializeSearch()
    }
}

export function initializeReactComponents(root = undefined) {
    (root? root : document).querySelectorAll(".kars-react-component").forEach((C) => {
        const Klass = Infra.componentRegistry[C.dataset.componentClass]
        if (!Klass) {
            console.warn(`Couldn't look up a class for ${C.dataset.componentClass}`)
            return
        }

        let compo
        if (Klass.defrost) {
            compo = Klass.defrost(Klass, C)
        } else {
            compo = <Klass />
        }

        ReactDOM.render(<Provider store={Infra.store}>
            {compo}
        </Provider>, C)
    })
}

function bindAppearanceToggle(node) {
    node.addEventListener("click", dmToggleAppearance, false)
    node.tabIndex = 0
    node.addEventListener("keydown", (e) => {
        if (e.keyCode == 0x0d || e.keyCode == 0x20) {
            e.preventDefault()
            dmToggleAppearance()
        }
    }, {passive: false})
}

function dmToggleAppearance() {
    const theme = Infra.store.getState().appearance.theme
    let nextAppearance

    if (theme === "system") {
        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            nextAppearance = "light"
        } else {
            nextAppearance = "dark"
        }
    } else {
        nextAppearance = theme === "dark"? "light" : "dark"
    }

    requestStoragePermission("site-theme").then((canProceed) => {
        if (canProceed)
            Infra.store.dispatch({type: `${Appearance.actions.setTheme}`, payload: nextAppearance})
    })
}

function didChange(prev, next) {
    let diff = false
    for (let key of Object.keys(next)) {
        if (next[key] !== prev[key]) {
            diff = true
            break
        }
    }
    return diff
}

function init() {
    Infra.store.injectReducers({
        album: Album.AlbumStore.reducer,
    })

    let appearance = {}
    Infra.store.subscribe(() => {
        const state = Infra.store.getState().appearance
        if (!didChange(appearance, state)) {
            return
        }
        appearance = state

        if (Infra.canWritebackState() && hasStoragePermission()) {
            localStorage.setItem("as$$appearance", JSON.stringify(state))         
        }
    })

    Infra.registerComponents({
        CardDisplayModeSwitcher,
        ImageSwitcher,
        SkillTree: SkillTreeLoader,
        MemberListDisplaySwitcher,
    })

    TLInject.initialize()
    initLangMenu()
    GutterMenu.injectIntoPage()
    NavMenu.injectIntoPage()

    Infra.initialize().then(() => {
        console.debug("Localizations have arrived. Continuing...")
        initializeContextDependentModules().then(() => {
            initializeReactComponents()
            Infra.enableStateWriteback()
        })
    })

    if (Experiments.readFeatureFlagsInsecure() & FLG_CS_SHOW_DEV_INFO_E) {
        document.body.dataset.developer = "true"
    }

    bindAppearanceToggle(document.querySelector("#bind-appearance-toggle"))
}

if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", init)
} else {
    init()
}
