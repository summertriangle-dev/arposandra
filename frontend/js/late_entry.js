import React from "react"
import ReactDOM from "react-dom"
import {Provider} from "react-redux"

import Infra from "./infra"
import * as TLInject from "./tlinject"
import * as Album from "./album"
import * as NewsFilter from "./news_filter"
import * as Experiments from "./experiments"
import { SaintUserConfig } from "./event-tracker/event_tracker_internal"
import { CardDisplayModeSwitcher, ImageSwitcher } from "./card_page_components"
import SkillTree from "./skill_tree"
import { StoryViewer } from "./transcript"
import { initLangMenu } from "./lang_menu"

const ReactComponentClassRegistry = {    
    CardDisplayModeSwitcher,
    ImageSwitcher,
    SkillTree,
    NewsFilterSwitch: NewsFilter.NewsFilterSwitch,
    StoryViewer,
}

function initializeContextDependentModules() {
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
}

function initializeReactComponents() {
    document.querySelectorAll(".kars-react-component").forEach((C) => {
        const Klass = ReactComponentClassRegistry[C.dataset.componentClass]
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

function init() {
    Infra.store.injectReducers({
        album: Album.AlbumStore.reducer,
        newsFilter: NewsFilter.NewsFilter.reducer,
        saint: SaintUserConfig.reducer
    })
    TLInject.initialize()
    NewsFilter.initWithRedux(Infra.store)
    initLangMenu()

    Infra.initialize().then(() => {
        console.debug("Localizations have arrived. Continuing...")
        initializeContextDependentModules()
        initializeReactComponents()

        Infra.enableStateWriteback()
    })
}

if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", init)
} else {
    init()
}
