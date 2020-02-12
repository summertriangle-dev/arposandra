import {ModalManager} from "./modals"
import React from "react"

export function injectIntoPage() {
    document.querySelector("#uilib-modal-button").addEventListener("click", () => {
        ModalManager.pushModal(() => {
            return <p>hello!</p>
        })
    }, {passive: true})
}