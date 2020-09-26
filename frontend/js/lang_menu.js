import React from "react"
import Infra from "./infra"
import Cookies from "js-cookie"

import { ModalManager } from "./modals"
import { requestStoragePermission } from "./storage_permission"

function loadLanguages() {
    const xhr = new XMLHttpRequest()
    return new Promise((resolve, reject) => {
        xhr.onreadystatechange = () => {
            if (xhr.readyState !== 4) return

            if (xhr.status == 200) {
                const json = JSON.parse(xhr.responseText)
                resolve(json)
            } else {
                reject()
            }
        }
        xhr.open("GET", "/api/private/langmenu.json")
        xhr.send()
    })
}

function localizeReturnedLanguageList(langs) {
    return {
        siteLangs: langs.languages.map((code) => {
            return {
                code: code,
                name: Infra.strings["TLInject.localizedLanguages"][code]
            }
        }),
        dataLangs: langs.dictionaries.map((ob) => {
            return {
                code: ob.code,
                name: Infra.strings.formatString(
                    Infra.strings.LangMenu.DictionaryFormat,
                    ob.code, ob.name
                )
            }
        }),
        regions: langs.regions
    }
}

function regionAwareReload() {
    const regionedPaths = ["news", "events", "history"]
    const paths = window.location.pathname.split("/")
    if (paths.length > 2 && regionedPaths.includes(paths[2])) {
        window.location.href = `/${paths[2]}`
        return
    }

    window.location.reload()
}

class LanguageMenu extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            lang: document.querySelector("html").lang,
            dictionary: Cookies.get("mdic"),
            region: Cookies.get("dsid"),
            fullListAvailable: false,
            siteLangs: [],
            dataLangs: [],
            regions: []
        }

        loadLanguages().then((l) => {
            this.setState(localizeReturnedLanguageList(l), () => this.fixDefaults())
        })
    }

    fixDefaults() {
        this.setState({
            dictionary: Cookies.get("mdic") || this.state.dataLangs[0].code,
            region: Cookies.get("dsid") || this.state.regions[0],
        })
    }

    save() {
        requestStoragePermission().then((canProceed) => {
            if (canProceed) {
                Cookies.set("lang", this.state.lang, {expires: 1333337})
                Cookies.set("mdic", this.state.dictionary, {expires: 1333337})
                Cookies.set("dsid", this.state.region, {expires: 1333337})
                setTimeout(regionAwareReload, 200)
            }

            this.props.dismiss()
        })        
    }

    goToExperiments() {
        window.location.href = "/experiments"
    }

    render() {
        return <section className="modal-body tlinject-modal">
            <h2 className="h5 mb-1">{Infra.strings.LangMenu.ModalTitle}</h2>
            <div className="form-group">
                <label htmlFor="ui-language-select">
                    {Infra.strings.LangMenu.UILanguageSelectLabel}
                </label>
                <select name="ui-language-select" className="custom-select form-control"
                    value={this.state.lang}
                    onChange={(e) => this.setState({lang: e.target.value})}>
                    {this.state.siteLangs.map((l) =>
                        <option key={l.code} value={l.code}>{l.name}</option>)}
                </select>
            </div>
            <div className="form-group">
                <label htmlFor="dict-select">
                    {Infra.strings.LangMenu.DictionarySelectLabel}
                </label>
                <select name="dict-select" className="custom-select form-control"
                    value={this.state.dictionary}
                    onChange={(e) => this.setState({dictionary: e.target.value})}>
                    {this.state.dataLangs.map((l) =>
                        <option key={l.code} value={l.code}>{l.name}</option>)}
                </select>
            </div>
            <div className="form-group">
                <label htmlFor="region-select">
                    {Infra.strings.LangMenu.RegionSelectLabel}
                </label>
                <select name="region-select" className="custom-select form-control"
                    value={this.state.region}
                    onChange={(e) => this.setState({region: e.target.value})}>
                    {this.state.regions.map((rgnCode) =>
                        <option key={rgnCode} value={rgnCode}>{rgnCode}</option>)}
                </select>
            </div>
            <div className="form-row kars-fieldset-naturalorder">
                <button className="item btn btn-primary"
                    onClick={() => this.save()}>{Infra.strings.LangMenu.Save}</button>
                <button className="item btn btn-secondary"
                    onClick={this.props.dismiss}>{Infra.strings.LangMenu.Cancel}</button>
                <span className="item flexible-space"></span>
                <a className="item btn btn-secondary" href="/experiments">
                    {Infra.strings.LangMenu.GoToExperiments}</a>
            </div>
        </section>
    }
}


////////////////////////////////////////////////////

export function initLangMenu() {
    document.getElementById("bind-languagemenu-toggle").addEventListener("click", () => {
        ModalManager.pushModal((dismiss) => <LanguageMenu dismiss={dismiss} />)
    }, {passive: true})
}