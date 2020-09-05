import {ModalManager} from "./modals"
import React from "react"
import Cookies from "js-cookie"
import { requestStoragePermission } from "./storage_permission"

// Do not localize anything in this file.

export const FLG_CS_SHOW_DEV_INFO_E = 0x2

async function _validateCaveSlimeEntry(password) {
    if (!await requestStoragePermission()) {
        return
    }

    const p = new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.onreadystatechange = () => {
            if (xhr.readyState == 4) {
                if (xhr.status == 200) {
                    resolve(JSON.parse(xhr.responseText))
                } else {
                    reject()
                }
            }
        }
        xhr.open("POST", "/api/private/change_experiment_flags", true)
        xhr.send(JSON.stringify({ password }))
    })

    let retVal
    try {
        retVal = await p
    } catch {
        document.querySelector("#cs-input").value = ""
        return
    }

    ModalManager.pushModal((dismiss) => {
        return <section className="modal-body tlinject-modal">
            <p>{retVal.message}</p>
            <div className="form-row kars-fieldset-naturalorder">
                <button className="item btn btn-primary" onClick={dismiss}>Dismiss</button>
            </div>
        </section>
    })
}

function displayEntitlementsModal() {
    ModalManager.pushModal(() => {
        const ff = readFeatureFlagsInsecure()
        return <div className="modal-body">
            <p>Entitled to use CaveSlime: 
                {ff & 0x1? " Yes" : " No"}</p>
            <p>Developer info feature flag:
                {ff & FLG_CS_SHOW_DEV_INFO_E? " Yes" : " No"}</p>
            <p>Have consent for cookies/local storage:
                {localStorage.getItem("as$have-storage-consent") !== null? " Yes" : " No"}</p>
        </div>
    })
}

export function injectIntoPage() {
    document.querySelector("#uilib-modal-button").addEventListener("click", () => {
        ModalManager.pushModal(() => {
            return <p>hello! <button onClick={() => {
                ModalManager.pushModal(() => {
                    return <p>Modal in modal test</p>
                })
            }}>Wow! Show me another</button></p>
        })
    }, {passive: true})

    document.querySelector("#cs-submit-button").addEventListener("click", () => {
        _validateCaveSlimeEntry(document.querySelector("#cs-input").value)
    }, {passive: true})

    document.querySelector("#cs-test-permission").addEventListener("click", () => {
        requestStoragePermission().then((val) => {
            ModalManager.pushModal(() => {
                return <p>User response: {val? "YES" : "NO"}</p>
            })
        })
    }, {passive: true})
    document.querySelector("#cs-test-permission-f").addEventListener("click", () => {
        requestStoragePermission(null, true).then((val) => {
            ModalManager.pushModal(() => {
                return <p>User response: {val? "YES" : "NO"}</p>
            })
        })
    }, {passive: true})
    document.querySelector("#cs-check-ff-status").addEventListener("click", displayEntitlementsModal, {passive: true})
}

export function readFeatureFlagsInsecure() {
    const cookieValue = Cookies.get("cs_fflg_v2")
    if (!cookieValue) {
        return 0
    }

    const vals = cookieValue.split("|")
    if (vals.length != 6) {
        return 0
    }

    const [dataLength, dataValue] = vals[4].split(":")
    if (!dataValue || dataValue.length != parseInt(dataLength)) {
        return 0
    }

    return parseInt(atob(dataValue)) || 0
}