import React, { Fragment } from "react"
import ReactDOM from "react-dom"
import Infra from "./infra"

class PASearchContext {
    constructor() {
        this.schema = null
        this.lastError = null
        this.queryTemplate = []
        this.queryValues = {}
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

    renderCriteriaList() {
        const boundAddCriteria = this.addCriteriaAction.bind(this)
        const node = document.getElementById("criteria-list-host")
        if (this.queryTemplate.length > 0) {
            node.className = "col-md-6"
        } else {
            node.className = "col-12"
        }

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
            ReactDOM.render(<PAQueryEditor schema={this.schema} query={this.queryTemplate} />, 
                document.getElementById("query-editor-host"), resolve)
        })
    }

    sendSchemaRequest(toUrl) {
        // return Promise.reject({
        //     "error": "http(403)"
        // })

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                console.debug("Panther: did finish loading schema with result: " + xhr.status)
                if (xhr.status == 200) {
                    resolve(JSON.parse(xhr.responseText))
                } else {
                    reject({"error": `http(${xhr.status})`})
                }
            }
            xhr.open("GET", toUrl)
            xhr.send()
        })
    }

    async reloadSchema(fromUrl) {
        const schemaP = this.sendSchemaRequest(fromUrl)

        try {
            this.schema = await schemaP
            this.lastError = null
        } catch (rejection) {
            this.lastError = rejection
        }

        this.queryTemplate = Object.keys(this.schema.criteria)
        this.renderCriteriaList()
        this.renderQueryEditor()
    }
}

const context = new PASearchContext()

class PAQueryEditor extends React.Component {
    constructor(props) {
        super(props)
        this.state = {queryValues: {}}
    }

    renderEnumInput(k, criteria) {
        if (criteria.behaviour && criteria.behaviour.compare_type === "bit-set") {
            return <div className="col-8">
                {criteria.choices.map((choice) => {
                    const key = `criteria-${k}-choice-${choice.name}`
                    return <div key={key} className="form-check form-check-inline">
                        <input id={key} className="form-check-input" type="checkbox" value={choice.value} checked />
                        <label htmlFor={key} className="form-check-label">{choice.display_name || choice.name}</label>
                    </div>
                })}
            </div>
        }
    
        return <div className="col-8">
            <select id={`input-for-${k}`} className="custom-select">
                {criteria.choices.map((choice) => 
                    <option key={choice.value} value={choice.value}>{choice.display_name || choice.name}</option>
                )}
            </select>
        </div>
    }

    renderNumericInput(k, criteria) {
        if (criteria.behaviour && criteria.behaviour.compare_type === "equal") {
            return <div className="col-8"><input id={`input-for-${k}`}
                className="form-control" 
                type="text" pattern="[0-9]*" 
                placeholder={criteria.display_name} />
            </div>
        }

        return <>
            <div className="col-2"><select className="custom-select">
                <option value="gt">&gt;</option>
                <option value="lt">&lt;</option>
                <option value="eq">=</option>
            </select></div>
            <div className="col-6"><input id={`input-for-${k}`}
                className="form-control" 
                type="text" pattern="[0-9]*" 
                placeholder={criteria.display_name} /></div>    
        </>
    }

    renderSingleEditor(k, criteria) {
        let input

        switch(criteria.type) {
        case 1:
            input = this.renderNumericInput(k, criteria)
            break
        case 3:
            input = <div className="col-8"><input id={`input-for-${k}`}
                className="form-control" 
                type="date" 
                placeholder={criteria.display_name} />
            </div>
            break
        case 2:
        case 4:
            input = <div className="col-8"><input id={`input-for-${k}`}
                className="form-control" 
                type="text" 
                placeholder={criteria.display_name} 
                maxLength={criteria.max_length} />
            </div>
            break
        case 5:
            input = <div className="col-8"><i className="icon ion-ios-hand"></i></div>
            break
        case 1000:
        case 1001:
            input = this.renderEnumInput(k, criteria)
            break
        }

        return <div key={k} className="query-editor-row form-group row">
            <div className="col-4 col-form-label">
                <label className="mb-0" htmlFor={`input-for-${k}`}>{criteria.display_name || k}</label>
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
    return <div className="text-center">
        Error: {props.error.error}. Retry?
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
        return <div className="criteria-list">
            {Object.keys(this.props.schema.criteria).map(
                (k) => this.renderSingleCriteriaButton(k, this.props.schema.criteria[k])
            )}
        </div>
    }
}

export function initializeSearch() {
    context.reloadSchema("/api/private/search/cards/bootstrap.json")
}