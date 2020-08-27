import { ModalManager } from "./modals"
import React from "react"
import Infra from "./infra"

let requestedThisSession = []

export async function requestStoragePermission(forCategory, force) {
    if (localStorage.getItem("as$have-storage-consent") && !force) {
        return Promise.resolve(true)
    }

    if (forCategory) {
        if (requestedThisSession.indexOf(forCategory) !== -1) {
            return Promise.resolve(false)
        } else {
            requestedThisSession.push(forCategory)
        }
    }

    return new Promise((resolve) => {
        ModalManager.pushModal((dismiss) => {
            const dismissReturn = (v) => {
                resolve(v)
                dismiss()
            }

            return <section className="modal-body">
                <h2 className="h5 mb-3">{Infra.strings.StoragePermission.RequestTitle}</h2>
                {Infra.strings.StoragePermission.RequestBody.map((v, i) => <p key={i}>{v}</p>)}
                <div className="form-row kars-fieldset-naturalorder">
                    <button className="item btn btn-primary"
                        onClick={() => dismissReturn(true)}>{Infra.strings.StoragePermission.AllowButton}</button>
                    <button className="item btn btn-secondary"
                        onClick={() => dismissReturn(false)}>{Infra.strings.StoragePermission.DenyButton}</button>
                </div>
            </section>
        }).allowsImplicitDismiss(false).onBeginDismiss(() => resolve(false))
    }).then((val) => {
        if (val) {
            localStorage.setItem("as$have-storage-consent", "yes")
        } else {
            localStorage.removeItem("as$have-storage-consent")
        }
        return val
    })
}

export function hasStoragePermission() {
    if (localStorage.getItem("as$have-storage-consent")) {
        return true
    }
    return false
}
