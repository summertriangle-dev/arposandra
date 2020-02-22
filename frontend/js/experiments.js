import {ModalManager} from "./modals"
import React from "react"
import Cookies from "js-cookie"

// Do not localize anything in this file.

export const FLG_CS_AR_E = 0x1

function _validateCaveSlimeEntry(password) {
    let flags = Cookies.get("cs_fflg")
    if (flags === null) {
        flags = 0
    } else {
        flags = parseInt(flags)
    }

    if (password === "11162029") {
        let msg
        if (flags & FLG_CS_AR_E) {
            msg = "It sounds like the mechanism has returned to its normal position."
        } else {
            msg = "It sounds like something heavy moved from deeper inside the cave!"
        }

        flags ^= FLG_CS_AR_E

        ModalManager.pushModal((dismiss) => {
            return <section className="modal-body tlinject-modal">
                <p>{msg}</p>
                <div className="form-row kars-fieldset-naturalorder">
                    <button className="item btn btn-primary" onClick={dismiss}>Dismiss</button>
                </div>
            </section>
        })
    } 

    Cookies.set("cs_fflg", flags.toString(), {expires: 133337})
}

export function injectIntoPage() {
    document.querySelector("#uilib-modal-button").addEventListener("click", () => {
        ModalManager.pushModal(() => {
            return <p>hello!</p>
        })
    }, {passive: true})

    document.querySelector("#cs-submit-button").addEventListener("click", () => {
        _validateCaveSlimeEntry(document.querySelector("#cs-input").value)
    }, {passive: true})
}