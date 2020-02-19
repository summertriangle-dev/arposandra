import React from "react"
import Infra from "./infra"
import { ModalManager } from "./modals"

let config = {
    language: null,
    enableOnPage: false,
    isEnabledNow: false
}

function bootstrapAPI() {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open("GET", "/api/private/tlinject/bootstrap.json", true)
        xhr.onreadystatechange = () => {
            if (xhr.readyState == 4) {
                const j = JSON.parse(xhr.responseText)
                if (xhr.status == 200) {
                    resolve(j.result)
                } else {
                    reject(j.error)
                }
            }
        }
        xhr.send()
    })
}

function sendStringAPI(key, translated, assr) {
    if (!config.language) {
        return Promise.reject("TLInject was invoked before it was ready. You should never see this message.")
    }

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open("POST", `/api/private/tlinject/${config.language}/submit.json`, true)
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.onreadystatechange = () => {
            if (xhr.readyState == 4) {
                const j = JSON.parse(xhr.responseText)
                if (xhr.status == 200) {
                    resolve(j.results)
                } else {
                    reject(j.error)
                }
            }
        }
        xhr.send(JSON.stringify({key, assr, translated}))
    })
}

function loadStringsAPI(trans) {
    if (!config.language) {
        return Promise.reject("TLInject was invoked before it was ready. You should never see this message.")
    }

    if (trans.length == 0) {
        return Promise.resolve({})
    }

    return new Promise((resolve) => {
        const xhr = new XMLHttpRequest()
        xhr.open("POST", `/api/private/tlinject/${config.language}/strings.json`, true)
        xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8")
        xhr.onreadystatechange = () => {
            if (xhr.readyState == 4 && xhr.status == 200) {
                const returned_list = JSON.parse(xhr.responseText)
                resolve(returned_list.results)
            }
        }
        xhr.send(JSON.stringify(trans))
    })
}

async function getSupportedLanguages() {
    const cached = localStorage.getItem("as$tliLang")
    let values
    if (cached) {
        try {
            values = JSON.parse(cached)
        } catch {
            values = null
        }
    }

    if (values && Date.now() - values.t > 86400000) {
        values = null
    }

    if (values) {
        return values.l
    } else {
        const results = await bootstrapAPI()
        localStorage.setItem("as$tliLang", JSON.stringify({
            l: results.languages, 
            t: Date.now()
        }))
        return results.languages
    }
}

class TLInjectInputPromptModal extends React.Component {
    constructor(props) {
        super(props)
        this.state = {}
    }

    submit() {
        this.props.submitString(this, this.state.tstring || "", this.props.abort)
    }

    cancel() {
        this.props.abort(this)
    }

    submitExplicitClear() {
        this.props.submitString(this, null, this.props.abort)
    }

    bottomText() {
        if (this.props.isMock) {
            return Infra.strings["TLInject.CurrentSubmissionIsMock"]
        }

        if (this.state.displayError) {
            return this.state.displayError
        }

        return Infra.strings.formatString(Infra.strings["TLInject.HelpText"],
            <a target="_blank" rel="noopener" href="/static/tl_help.html">
                {Infra.strings["TLInject.HelpLinkPlaceholder"]}</a>)
    }

    render() {
        return <section className="modal-body tlinject-modal">
            <p>
                {Infra.strings.formatString(Infra.strings["TLInject.SubmissionPrompt"],
                    this.props.langName, <b>{this.props.originalText}</b>)}
            </p>
            <div className="form-group">
                <div className="control">
                    <input className="form-control" type="text"
                        placeholder={Infra.strings["TLInject.InputFieldPlaceholder"]}
                        onChange={(e) => this.setState({tstring: e.target.value})} />
                </div>
                <small className="form-text text-muted">
                    {this.bottomText()}
                </small>
            </div>
            <div className="form-row kars-fieldset-naturalorder">
                <button className="item btn btn-primary"
                    disabled={! (this.state.tstring && this.state.tstring.trim())}
                    onClick={() => this.submit()}>{Infra.strings["TLInject.Submit"]}</button>
                <button className="item btn btn-secondary"
                    onClick={() => this.cancel()}>{Infra.strings["TLInject.Cancel"]}</button>
                <span className="item flexible-space"></span>
                <button className="item btn btn-danger"
                    onClick={() => this.submitExplicitClear()}>{Infra.strings["TLInject.ExplicitClear"]}</button>
            </div>
        </section>
    }
}


// FIXME: Need to wait for localizations
function displayStringSubmissionUI(forNode) {
    const key = forNode.dataset.tlik || forNode.dataset.originalString
    const orig = forNode.dataset.originalString
    const assr = forNode.dataset.assr
    const isMock = forNode.dataset.mock? true : false

    const submitString = (component, string, dismiss) => {
        let p
        if (isMock) {
            console.debug("Mock TLInject submissions are not sent to the server.")
            p = Promise.resolve({[key]: string})
        } else {
            p = sendStringAPI(key, string, assr)
        }

        p.then((stringDict) => {
            insertTranslations(stringDict)
            dismiss()
        }).catch((errorString) => {
            component.setState({displayError: errorString})
        })
    }

    ModalManager.pushModal((dismiss) => 
        <TLInjectInputPromptModal 
            originalText={orig}
            langName={Infra.strings["TLInject.localizedLanguages"][config.language]}
            submitString={submitString}
            abort={dismiss}
            isMock={isMock}
        />
    )
}

function insertTranslations(table) {
    const strings = document.getElementsByClassName("tlinject")
    if (strings.length === 0) return

    for (let i = 0; i < strings.length; ++i) {
        const node = strings[i]

        const key = node.dataset.tlik
        if (Object.hasOwnProperty.call(table, key)) {
            node.textContent = table[key] !== null? table[key] : node.dataset.originalString
        }
    }
}

const tli_click_handler = (e) => {
    e.preventDefault()
    displayStringSubmissionUI(e.target)
}
function setupDOM() {
    let tls = []
    const strings = document.getElementsByClassName("tlinject")
    if (strings.length === 0) return []

    for (let i = 0; i < strings.length; i++) {
        const element = strings[i]

        const key = element.dataset.tlik || element.textContent
        if (!element.hasAttribute("data-tlik")) {
            element.setAttribute("data-tlik", key)
        }

        if (!element.dataset.mock && tls.indexOf(key) === -1) {
            tls.push(key)
        }

        if (!element.hasAttribute("data-original-string")) {
            element.setAttribute("data-original-string", element.textContent.trim())
        }

        if (element.hasAttribute("data-assr") && !element.hasAttribute("data-bound")) {
            element.setAttribute("data-bound", "1")
            element.addEventListener("click", tli_click_handler, false)
        }
    }
    return tls
}

function defaultEnableOnPage() {
    const userPref = navigator.languages? navigator.languages[0] : navigator.language
    if (userPref.match(/^ja([^a-zA-Z]|$)/)) {
        return false
    }
    return true
}

function applyConfigChange() {
    if (config.enableOnPage === config.isEnabledNow) {
        return
    }

    if (config.enableOnPage) {
        console.debug("TLInject: setting up!!")
        const tls = setupDOM()
        loadStringsAPI(tls).then((t) => insertTranslations(t))
    } else {
        console.debug("TLInject: reverting all strings for config change")
        const strings = document.getElementsByClassName("tlinject")

        for (let i = 0; i < strings.length; i++) {
            const element = strings[i]
            if (element.dataset.originalString) {
                element.textContent = element.dataset.originalString
            }
        }
    }

    config.isEnabledNow = config.enableOnPage
}

export function initialize() {
    const updateConfigFromRedux = () => {
        const v = Infra.store.getState().appearance.tliEnable
        if (v !== null && v !== undefined) {
            config.enableOnPage = v
        } else {
            config.enableOnPage = defaultEnableOnPage()
        }

        applyConfigChange()
    }

    getSupportedLanguages().then((langs) => {
        if (langs.indexOf(Infra.getDocumentLocale()) !== -1) {
            config.language = Infra.getDocumentLocale()
        } else {
            config.language = langs[0]
        }

        updateConfigFromRedux()
        Infra.store.subscribe(updateConfigFromRedux)
    })
}
