import React from "react"
import ReactDOM from "react-dom"
import Infra from "../infra"
import { ModalManager } from "../modals"
// import { PAWordCompletionist } from "./completionist"
import { PAFakeSearchButton, PAPageControl, PAQueryEditor } from "./components"
import { serializeQuery, deserializeQuery, /* simulatedNetworkDelay */ } from "./util"

const PASearchProgressState = {
    LoadingSchema: 0,
    EditingQuery: 1,
    Searching: 2,
    LoadingResults: 3,
    ContinueSearch: 4,
}

const RESULTS_PER_PAGE = 12

class PASearchContext {
    constructor() {
        this.schema = null
        this.dictionary = null

        this.currentQuery = null
        this.currentSort = null
        this.currentResults = []
        this.currentPage = 0

        this.flightState = PASearchProgressState.LoadingSchema
        this.isFirstLoad = true
    }

    transitionToState(state) {
        console.debug("Panther: moving to UI state", state)
        this.flightState = state

        if (this.flightState == PASearchProgressState.LoadingResults
            || this.flightState == PASearchProgressState.Searching) {
            // Provide some indication that the current display is stale.
            const host = document.getElementById("results-host")
            host.style.opacity = 0.5

            const pager = document.getElementById("pager-host")
            ReactDOM.render(<PAPageControl 
                disabled={true}
                page={this.currentPage + 1} 
                pageCount={this.pageCount()} 
                moveToPage={this.moveToPageAction.bind(this)} />, pager)
        }

        this.render()
    }

    render() {
        const placement = document.getElementById("query-editor-host")
        let widget = null

        switch (this.flightState) {
        case PASearchProgressState.LoadingSchema:
            widget = <>
                <PAFakeSearchButton />
                <div className="text-center">
                    <span className="h6">{Infra.strings.Search.StateMessage.LoadingSchema}</span>
                </div>
            </>
            break
        case PASearchProgressState.EditingQuery:
            widget = <PAQueryEditor 
                schema={this.schema} 
                query={this.currentQuery}
                sortBy={this.currentSort}
                performSearchAction={this.performSearchAction.bind(this)} />
            break
        case PASearchProgressState.ContinueSearch:
            widget = <div className="text-center">
                <i className="icon ion-ios-search"></i>
                <a className="h6" onClick={(e) => { 
                    e.preventDefault()
                    this.transitionToState(PASearchProgressState.EditingQuery) 
                }} href="#">{Infra.strings.Search.StateMessage.Continue}</a>         
            </div>
            break
        case PASearchProgressState.Searching:
            widget = <PAGenericMessage message={Infra.strings.Search.StateMessage.Searching} />
            break
        case PASearchProgressState.LoadingResults:
            widget = <PAGenericMessage message={Infra.strings.Search.StateMessage.LoadingCards} />
            break
        }

        ReactDOM.render(widget, placement)
    }

    displayErrorModal(message) {
        ModalManager.pushModal((dismiss) => {
            return <section className="modal-body">
                <p>{message}</p>
                <div className="form-row kars-fieldset-naturalorder">
                    <button className="item btn btn-primary" 
                        autoFocus={true}
                        onClick={dismiss}>{Infra.strings.Search.DismissErrorModal}</button>
                </div>
            </section>
        })
    }

    performSearchAction(query, sortBy) {
        if (Object.keys(query).length == 0) {
            return this.displayErrorModal(Infra.strings.Search.Error.NoCriteriaValues)
        }

        const nq = {_sort: sortBy}
        Object.assign(nq, query)

        const hash = serializeQuery(this.schema, nq)
        history.replaceState(null, document.title, window.location.href.split("#")[0] + "#" + hash)
        this.currentQuery = query
        this.currentSort = sortBy

        this.transitionToState(PASearchProgressState.Searching)
        this.sendSearchRequest(nq).catch((error) => {
            this.displayErrorModal(Infra.strings.formatString(
                Infra.strings.Search.Error.ExecuteFailed,
                error.error
            ))
            this.transitionToState(PASearchProgressState.EditingQuery)
        }).then((results) => {
            if (!results) {
                return
            }

            this.displayResultList(results.result || [], 0)
        })
    }

    historyBackAction(event) {
        if (event.state) {
            this.displayResultList(event.state.results, event.state.page)
        }
    }

    moveToPageAction(pNum) {
        window.scrollTo(0, 0)
        // uhh....
        console.log(`${document.querySelector("title").textContent} (${pNum}/${this.pageCount()})`)
        history.pushState(
            {results: this.currentResults, page: pNum - 1}, 
            `${document.title} (${pNum}/${this.pageCount()})`,
            window.location.href)

        this.displayResultList(this.currentResults, pNum - 1, false)
    }

    pageCount() {
        return Math.ceil(this.currentResults.length / RESULTS_PER_PAGE)
    }

    async displayResultList(results, page, editHistory=true) {
        this.currentResults = results
        this.currentPage = page || 0

        if (this.currentResults.length > 0) {
            this.transitionToState(PASearchProgressState.LoadingResults)

            if (editHistory) {
                history.replaceState(
                    {results: this.currentResults, page: this.currentPage}, 
                    document.title, window.location.href)
            }

            const idl = this.currentResults.slice(this.currentPage * RESULTS_PER_PAGE, 
                (this.currentPage + 1) * RESULTS_PER_PAGE)
            
            // ----- async break point -----
            const doc = await this.sendAjaxCardRequest(idl)    

            this.transitionToState(PASearchProgressState.ContinueSearch)
            const host = document.getElementById("results-host")
            const incoming = doc.getElementById("results-host")
            incoming.parentNode.removeChild(incoming)
            host.parentNode.insertBefore(incoming, host)
            host.parentNode.removeChild(host)

            const pager = document.getElementById("pager-host")
            ReactDOM.render(
                <PAPageControl page={this.currentPage + 1} 
                    pageCount={this.pageCount()} 
                    moveToPage={this.moveToPageAction.bind(this)} />,
                pager)
        } else {
            this.transitionToState(PASearchProgressState.EditingQuery)

            const host = document.getElementById("results-host")
            ReactDOM.render(<div className="text-center mb-5">
                <span className="h6">{Infra.strings.Search.Error.NoResults}</span>
            </div>, host)
        }
    }

    async sendAjaxCardRequest(cardIds) {
        // await simulatedNetworkDelay(1000)

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
        // await simulatedNetworkDelay(3000)

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
        // await simulatedNetworkDelay(500)

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
        this.transitionToState(PASearchProgressState.LoadingSchema)

        const schemaPs = Promise.all(overlayURLs.map((x) => this.sendSchemaRequest(x)))
        let schemas = null
        try {
            schemas = await schemaPs
            this.lastError = null
        } catch (rejection) {
            this.lastError = rejection
            this.transitionToState(PASearchProgressState.SchemaLoadFailed)
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

        const dictionaryP = this.sendSchemaRequest(dictionaryURL)
        try {
            const dict = await dictionaryP
            this.dictionary = dict
        } catch (rejection) {
            this.lastError = rejection
        }
    }

    performFirstLoadStateRestoration() {
        if (window.location.hash) {
            const queryFromURL = deserializeQuery(this.schema, window.location.hash.substring(1))
            this.currentSort = queryFromURL._sort
            delete queryFromURL["_sort"]
            this.currentQuery = queryFromURL
        }

        if (history.state && Array.isArray(history.state.results)) {
            this.displayResultList(history.state.results, history.state.page || 0)
        } else {
            this.transitionToState(PASearchProgressState.EditingQuery)
        }
    }
}

function PAGenericMessage(props) {
    return <div className="text-center">
        <i className="icon ion-ios-search"></i>
        <span className="h6">{props.message}</span>
    </div>
}

export function initializeSearch() {
    const context = new PASearchContext()
    context.reloadSchema(
        ["/static/search/base.en.json", "/static/search/skills.enum.en.json"], 
        "/static/search/dictionary.en.json"
    ).then(() => {
        context.performFirstLoadStateRestoration()
        window.addEventListener("popstate", context.historyBackAction.bind(context))
    })
    console.debug("The Panther context is:", context)
    console.debug("Happy debugging!")
}
