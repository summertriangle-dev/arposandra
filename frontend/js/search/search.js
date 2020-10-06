import React from "react"
import ReactDOM from "react-dom"
import Infra from "../infra"
import { ModalManager } from "../modals"
import { PAWordCompletionist } from "./completionist"

import { injectIntoPage as initializeAlbum } from "../album"
import { initializeReactComponents } from "../late_entry"

import { CONTROL_TYPE, PAEnumField, PANumericField } from "./components"

function isActivationKey(key) {
    return (key === "Enter" || key === " ")
}

class PASearchContext {
    constructor() {
        this.schema = null
        this.dictionary = null
        this.lastError = null
        this.queryTemplate = []
        this.queryValues = {}
        this.currentResults = []
        this.currentPage = 0
    }

    registerEvents() {
        console.debug("Panther: registering events")
        document.getElementById("criteria-finder").addEventListener("input", () => {
            this.renderCompletionist()
        })

        document.getElementById("search-button").addEventListener("click", (e) => {
            e.preventDefault()

            const hash = "#saved-state=" + btoa(JSON.stringify(this.queryValues))
            history.replaceState(null, document.querySelector("title").textContent, 
                window.location.href.split("#")[0] + hash)
            
            this.performSearch(this.queryValues)
        })
    }

    copyQueryAction(queryValues) {
        console.debug("Panther will copy query values:", queryValues)
        this.queryValues = {}
        Object.assign(this.queryValues, queryValues)
    }

    addCriteriaAction(event) {
        const name = event.currentTarget.dataset.selectedCriteriaId
        console.debug("Panther: add criteria id:", name)
        if (this.queryTemplate.indexOf(name) === -1) {
            this.queryTemplate.push(name)
        }

        this.renderCriteriaList()
        this.renderQueryEditor().then(() => {
            document.getElementById(`input-for-${name}`).focus()
        })
    }

    removeCriteriaAction(named) {
        if (this.queryTemplate.indexOf(named) >= 0) {
            this.queryTemplate.splice(this.queryTemplate.indexOf(named), 1)
        }

        this.renderCriteriaList()
        this.renderQueryEditor()
    }

    renderCriteriaList() {
        const boundAddCriteria = this.addCriteriaAction.bind(this)
        const node = document.getElementById("criteria-list-host")

        return new Promise((resolve) => {
            if (this.lastError) {
                ReactDOM.render(<PASchemaLoadErrorMessage error={this.lastError} />, 
                    node, resolve)
            } else {
                ReactDOM.render(<PACriteriaList
                    schema={this.schema} 
                    usedCriteria={this.queryTemplate}
                    addCriteriaAction={boundAddCriteria} />, 
                node, resolve)
            }
        })
    }

    renderQueryEditor() {
        return new Promise((resolve) => {
            ReactDOM.render(<PAQueryEditor 
                schema={this.schema} 
                query={this.queryTemplate} 
                removeCriteriaAction={this.removeCriteriaAction.bind(this)} 
                copyQueryAction={this.copyQueryAction.bind(this)} />, 
            document.getElementById("query-editor-host"), resolve)
        })
    }

    renderCompletionist() {
        if (!this.dictionary) return

        const textField = document.getElementById("criteria-finder")
        const parent = document.getElementById("completion-target")

        ReactDOM.render(<PAWordCompletionist partial={textField.value} dictionary={this.dictionary} />, parent)
    }

    displayErrorModal(message) {
        ModalManager.pushModal((dismiss) => {
            return <section className="modal-body">
                <p>{message}</p>
                <div className="form-row kars-fieldset-naturalorder">
                    <button className="item btn btn-primary" 
                        onClick={dismiss}>{Infra.strings.Search.DismissErrorModal}</button>
                </div>
            </section>
        })
    }

    performSearch(withParams) {
        if (Object.keys(withParams).length == 0) {
            return this.displayErrorModal(Infra.strings.Search.Error.NoCriteriaValues)
        }

        this.sendSearchRequest(withParams).catch((error) => {
            this.displayErrorModal(Infra.strings.formatString(
                Infra.strings.Search.Error.ExecuteFailed,
                error.error
            ))
        }).then((results) => {
            console.debug(results, Infra.strings.Search.Error.NoResults)
            if (results.result.length == 0) {
                this.displayErrorModal(Infra.strings.formatString(
                    Infra.strings.Search.Error.NoResults,
                    "<placeholder>"
                ))
            } else {
                this.displayResultList(results.result)
            }
        })
    }

    displayResultList(results) {
        this.currentResults = results

        document.body.classList.remove("editing-query")
        document.body.classList.add("viewing-results")

        const idl = this.currentResults.slice(this.currentPage * 10, (this.currentPage + 1) * 10)
        this.sendAjaxCardRequest(idl).then((doc) => {
            const host = document.querySelector("#results-host")
            const incoming = doc.getElementById("results-host")
            incoming.parentNode.removeChild(incoming)

            host.parentNode.insertBefore(incoming, host)
            host.parentNode.removeChild(host)

            initializeAlbum()
            console.log(initializeReactComponents)
            initializeReactComponents(incoming)
        })
    }

    async sendAjaxCardRequest(cardIds) {
        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.responseType = "document"
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                if (xhr.status == 200) {
                    resolve(xhr.responseXML)
                } else {
                    reject(xhr.status)
                }
            }
            xhr.open("GET", "/api/private/cards/ajax/" + cardIds.join(","))
            xhr.send()
        })
    }

    async sendSearchRequest(withParams) {
        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                if (xhr.status == 200) {
                    resolve(JSON.parse(xhr.responseText))
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText)
                        reject({error: err.error})
                        return
                    } catch {
                        reject({error: `http(${xhr.status})`})
                        return
                    }
                }
            }
            xhr.open("POST", "/api/private/search/cards/results.json")
            xhr.setRequestHeader("Content-Type", "application/json")
            xhr.send(JSON.stringify(withParams))
        })
    }

    async sendSchemaRequest(toUrl) {
        // return Promise.reject({
        //     "error": "http(403)"
        // })

        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                console.debug("Panther: did finish loading schema with result: " + xhr.status)
                if (xhr.status == 200) {
                    resolve(JSON.parse(xhr.responseText))
                } else {
                    reject({error: `http(${xhr.status})`, url: toUrl})
                }
            }
            xhr.open("GET", toUrl)
            xhr.send()
        })
    }

    async reloadSchema(overlayURLs, dictionaryURL) {
        const schemaPs = Promise.all(overlayURLs.map((x) => this.sendSchemaRequest(x)))
        let schemas = null
        try {
            schemas = await schemaPs
            this.lastError = null
        } catch (rejection) {
            this.lastError = rejection
        }

        if (schemas !== null) {
            this.schema = schemas[0]

            for (let i = 1; i < schemas.length; ++i) {
                const overlay = schemas[i].criteria
                for (let j in overlay) {
                    if (Object.hasOwnProperty.call(overlay, j)) {
                        Object.assign(this.schema.criteria[j], overlay[j])
                    }
                }
            }
        }

        this.renderCriteriaList()
        this.renderQueryEditor()

        const dictionaryP = this.sendSchemaRequest(dictionaryURL)
        try {
            const dict = await dictionaryP
            this.dictionary = dict
        } catch (rejection) {
            this.lastError = rejection
        }

        this.renderCompletionist()
    }
}

class PAQueryEditor extends React.Component {
    constructor(props) {
        super(props)
        this.state = {queryValues: {}}
    }

    componentDidUpdate() {
        const values = Object.keys(this.state.queryValues)
        let modified = false
        let queryValues = this.state.queryValues

        for (let i = 0; i < values.length; i++) {
            const element = values[i]

            if (this.props.query.indexOf(element) === -1) {
                delete queryValues[element]
                modified = true
            }
        }

        if (modified) {
            this.setState({queryValues}, () => this.props.copyQueryAction(this.state.queryValues))
        }
    }

    addValue(key, value) {
        const nextState = this.state.queryValues
        
        if (value === undefined) {
            delete nextState[key]
        } else {
            nextState[key] = value
        }

        this.setState({queryValues: nextState}, () => this.props.copyQueryAction(this.state.queryValues))
    }

    renderSingleEditor(k, criteria) {
        let input

        switch(criteria.type) {
        case CONTROL_TYPE.NUMBER:
            input = <PANumericField name={k} criteria={criteria}
                value={this.state.queryValues[k]} 
                changeValue={(k, v) => this.addValue(k, v)}/>
            break
        case CONTROL_TYPE.DATETIME:
            input = <div className="col-8">
                <input id={`input-for-${k}`}
                    className="form-control" 
                    type="date" 
                    placeholder={criteria.display_name} />
            </div>
            break
        case CONTROL_TYPE.STRING:
        case CONTROL_TYPE.STRING_MAX:
            input = <div className="col-8">
                <input id={`input-for-${k}`}
                    className="form-control" 
                    type="text" 
                    placeholder={criteria.display_name} 
                    maxLength={criteria.max_length} />
            </div>
            break
        case CONTROL_TYPE.COMPOSITE:
            input = <div className="col-8"><i className="icon ion-ios-hand"></i></div>
            break
        case CONTROL_TYPE.ENUM:
        case CONTROL_TYPE.ENUM_2:
            input = <PAEnumField name={k} 
                criteria={criteria} 
                value={this.state.queryValues[k]} 
                changeValue={(k, v) => this.addValue(k, v)}/>
            break
        }

        return <div key={k} className="query-editor-row form-group row">
            <div className="col-4 col-form-label">
                <label className="mb-0" htmlFor={`input-for-${k}`}>
                    <a tabIndex={0} 
                        onClick={() => this.props.removeCriteriaAction(k)}
                        onKeyPress={(e) => { if (isActivationKey(e.key)) this.props.removeCriteriaAction(k) }}>
                        <i className="icon icon ion-ios-close-circle text-danger" 
                            title={Infra.strings.Search.RemoveCriteria}></i>
                    </a>
                    {criteria.display_name || k}
                </label>
            </div>
            {input}
        </div>
    }

    render() {
        console.debug("[PAQueryEditor] query template:", this.props.query)
        return <div className="query-list">
            {this.props.query.map(
                (k) => this.renderSingleEditor(k, this.props.schema.criteria[k])
            )}
        </div>
    }
}

function PASchemaLoadErrorMessage(props) {
    return <div className="media mx-auto">
        <i className="icon icon-lg ion-ios-close-circle-outline text-danger pr-3"></i>
        <div className="media-body">
            <p className="m-0">
                {Infra.strings.formatString(Infra.strings.Search.Error.SchemaLoad, 
                    props.error.error, props.error.url)}
            </p>
            <p className="m-0">
                <a href="/">{Infra.strings.Search.SchemaLoadErrorTryAgain}</a>
            </p>
        </div>
    </div>
}

class PACriteriaList extends React.Component {
    constructor(props) {
        super(props)
    }

    iconClassForCriteriaName(name) {
        switch (name) {
        case "id":
            return "ion-ios-grid"
        case "ordinal":
            return "ion-ios-list"
        case "member":
            return "ion-ios-bowtie"
        case "max_appeal":
            return "ion-ios-happy"
        case "max_stamina":
            return "ion-ios-heart"
        case "max_technique":
            return "ion-ios-flash"
        case "member_group":
            return "ion-ios-people"
        case "member_subunit":
            return "ion-ios-ribbon"
        case "maximal_stat":
            return "ion-ios-podium"
        case "member_year":
            return "ion-ios-calendar"
        case "skill_major":
            return "ion-ios-color-wand"
        case "skill_minors":
            return "ion-ios-medkit"
        case "rarity":
            return "ion-ios-star"
        case "source":
            return "ion-ios-basket"
        case "role":
            return "ion-ios-move"
        case "attribute":
            return "ion-ios-color-palette"
        default:
            return "ion-ios-cube"
        }
    }

    renderSingleCriteriaButton(key, criteria) {
        if (this.props.usedCriteria.indexOf(key) !== -1) {
            return null
        }

        return <button key={key} data-selected-criteria-id={key} className="btn btn-secondary criteria-button"
            onClick={this.props.addCriteriaAction}>
            <p className="criteria-icon">
                <i className={`icon icon-lg ${this.iconClassForCriteriaName(key)}`}></i>
            </p>
            <p className="criteria-label">{criteria.display_name || key}</p>
        </button>
    }

    render() {
        if (Object.keys(this.props.schema.criteria).length == this.props.usedCriteria.length) {
            return null
        }

        return <div className="criteria-list pt-3">
            <p className="h6">{Infra.strings.Search.CriteriaBlocksTitle}</p>
            {Object.keys(this.props.schema.criteria).map(
                (k) => this.renderSingleCriteriaButton(k, this.props.schema.criteria[k])
            )}
        </div>
    }
}

export function initializeSearch() {
    const context = new PASearchContext()
    context.reloadSchema(
        ["/static/search/base.en.json", "/static/search/skills.enum.en.json"], 
        "/static/search/dictionary.en.json"
    ).then(() => context.registerEvents())
    console.debug("The Panther context is:", context)
    console.debug("Happy debugging!")
}
