import Infra from "./infra"
import * as Appearance from "./appearance"
import * as Timestamps from "./timestamps"

function init() {
    console.debug("Starting early init.")
    Appearance.initWithRedux(Infra.store)
    Timestamps.initialize()
}

if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", init)
} else {
    init()
}
