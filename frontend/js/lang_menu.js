import React from "react"
import Infra from "./infra"
import Cookies from "js-cookie"

import { ModalManager } from "./modals"

class LanguageMenu extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            lang: document.querySelector("html").lang,
            dictionary: Cookies.get("mdic"),
            siteLangs: [
                {code: "en", name: "English"},
                {code: "ja", name: "Japanese"},
            ],
            dataLangs: [
                {code: "ja", name: "Japanese (Original)"},
                {code: "en", name: "English (KLab EN)"},
            ]
        }
    }

    save() {
        console.debug("Saving...")
        Cookies.set("lang", this.state.lang, {expires: 1333337})
        Cookies.set("mdic", this.state.dictionary, {expires: 1333337})
        this.props.dismiss()

        setTimeout(() => window.location.reload(), 200)
    }

    render() {
        return <section className="modal-body tlinject-modal">
            <p className="font-weight-bold">Language Settings</p>
            <div className="form-group">
                <label htmlFor="ui-language-select">Use this language for site navigation:</label>
                <select name="ui-language-select" className="form-control" 
                    value={this.state.lang}
                    onChange={(e) => this.setState({lang: e.target.value})}>
                    {this.state.siteLangs.map((l) => 
                        <option key={l.code} value={l.code}>{l.name}</option>)}
                </select>
            </div>
            <div className="form-group">
                <label htmlFor="dict-select">Use this language for game data (including card and skill titles):</label>
                <select name="dict-select" className="form-control" 
                    value={this.state.dictionary}
                    onChange={(e) => this.setState({dictionary: e.target.value})}>
                    {this.state.dataLangs.map((l) => 
                        <option key={l.code} value={l.code}>{l.name}</option>)}
                </select>
            </div>
            <div className="form-row kars-fieldset-naturalorder">
                <button className="item btn btn-primary" 
                    onClick={() => this.save()}>Save and Reload</button>
                <button className="item btn btn-secondary" 
                    onClick={this.props.dismiss}>Cancel</button>
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