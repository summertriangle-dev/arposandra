import React from "react"
import ReactDOM from "react-dom"
import Infra from "../infra"
import { ModalManager } from "../modals"
import { PAFakeSearchButton, PAPageControl, PAQueryEditor } from "./components"
import { serializeQuery, deserializeQuery, isActivationKey, /* simulatedNetworkDelay */ } from "./util"
import { PACardSearchDomainExpert, PAAccessorySearchDomainExpert } from "./domain"

const PASearchProgressState = {
    LoadingSchema: 0,
    EditingQuery: 1,
    Searching: 2,
    LoadingResults: 3,
    ContinueSearch: 4,
    ErrorLoadingCards: 5,
    ErrorLoadingSchema: 6,
}

const RESULTS_PER_PAGE = 12

class PASearchContext {
    constructor(apiType) {
        this.schema = null
        this.dictionary = null

        this.currentQuery = null
        this.currentTemplate = null
        this.currentSort = null

        this.currentResults = []
        this.currentPage = 0

        this.flightState = PASearchProgressState.LoadingSchema
        this.isFirstLoad = true

        this.recoveryInfo = null
        this.inlineErrorMessage = null

        switch (apiType) {
        case "cards": this.api = new PACardSearchDomainExpert(); break
        case "accessories": this.api = new PAAccessorySearchDomainExpert(); break
        }
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
        case PASearchProgressState.ErrorZeroResults:
            widget = <PAQueryEditor 
                schema={this.schema} 
                query={this.currentQuery}
                template={this.currentTemplate}
                sortBy={this.currentSort}
                performSearchAction={this.performSearchAction.bind(this)}
                errorMessage={this.inlineErrorMessage}
                expert={this.api} />
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
        case PASearchProgressState.ErrorLoadingCards:
            widget = <PACardLoadErrorMessage 
                action={this.performErrorRecovery.bind(this)}
                editQueryAction={() => this.transitionToState(PASearchProgressState.EditingQuery)} />
            break
        case PASearchProgressState.ErrorLoadingSchema:
            widget = <PASchemaLoadErrorMessage 
                action={this.performErrorRecovery.bind(this)} />
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

    performSearchAction(query, sortBy, saveTemplate) {
        if (Object.keys(query).length == 0) {
            return this.displayErrorModal(Infra.strings.Search.Error.NoCriteriaValues)
        }

        const nq = {}
        Object.assign(nq, query)
        if (sortBy) {
            nq["_sort"] = sortBy
        }

        const hash = serializeQuery(this.schema, nq)
        // try not to clear the autosearch query
        if (!this.isFirstLoad) {
            history.pushState(null, document.title, this.currentURLBase() + "?" + hash)
        }
        this.currentQuery = query
        this.currentSort = sortBy
        this.currentTemplate = saveTemplate.slice(0)
        this.inlineErrorMessage = null

        this.transitionToState(PASearchProgressState.Searching)
        this.api.sendSearchRequest(nq).catch((error) => {
            this.displayResultList([], 0, true, error.error)
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
        history.pushState(
            {results: this.currentResults, page: pNum - 1}, 
            `${document.title} (${pNum}/${this.pageCount()})`,
            window.location.href)

        this.displayResultList(this.currentResults, pNum - 1, false)
    }

    currentURLBase() {
        return `${window.location.protocol}//${window.location.host}${window.location.pathname}`
    }

    pageCount() {
        return Math.ceil(this.currentResults.length / RESULTS_PER_PAGE)
    }

    async displayResultList(results, page, editHistory=true, error=null) {
        this.currentResults = results
        this.currentPage = page || 0

        const header = document.getElementById("info-host")
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
            let doc
            try {
                doc = await this.api.sendAjaxRequest(idl)
            } catch (rejectReason) {
                ReactDOM.render(null, header)
                ReactDOM.render(null, document.getElementById("results-host"))
                ReactDOM.render(null, document.getElementById("pager-host"))

                this.recoveryInfo = {results, page}
                this.transitionToState(PASearchProgressState.ErrorLoadingCards)
                return
            }

            this.transitionToState(PASearchProgressState.ContinueSearch)
            const host = document.getElementById("results-host")
            const incoming = doc.getElementById("results-host")
            incoming.parentNode.removeChild(incoming)
            host.parentNode.insertBefore(incoming, host)
            host.parentNode.removeChild(host)

            ReactDOM.render(
                <p>
                    {Infra.strings.formatString(
                        Infra.strings.Search.NumResultsLabel, 
                        Infra.strings.Search.NumResultsFormat(results.length))}
                </p>, header
            )

            const pager = document.getElementById("pager-host")
            ReactDOM.render(
                <PAPageControl page={this.currentPage + 1} 
                    pageCount={this.pageCount()} 
                    moveToPage={this.moveToPageAction.bind(this)} />,
                pager)
        } else {
            if (!error) {
                this.inlineErrorMessage = Infra.strings.Search.Error.NoResults
                this.transitionToState(PASearchProgressState.EditingQuery)
            } else {
                this.inlineErrorMessage = Infra.strings.formatString(
                    Infra.strings.Search.Error.ExecuteFailed, error)
                // No transition - it's handled in performSearchAction
            }

            const host = document.getElementById("results-host")
            host.className = ""
            host.style.opacity = 1.0

            ReactDOM.render(null, header)
            ReactDOM.render(null, host)
            ReactDOM.render(null, document.getElementById("pager-host"))
        }
    }

    async sendSchemaRequest(toUrl) {
        // await simulatedNetworkDelay(500)
        // return Promise.reject({error: "error", url: toUrl})

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
        } catch (rejection) {
            this.recoveryInfo = {overlayURLs, dictionaryURL}
            this.transitionToState(PASearchProgressState.ErrorLoadingSchema)
            return
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
            this.recoveryInfo = {overlayURLs, dictionaryURL}
            this.transitionToState(PASearchProgressState.ErrorLoadingSchema)
        }
    }

    performFirstLoadStateRestoration() {
        let auto = false
        let queryFromURL = null

        if (window.location.query) {
            queryFromURL = deserializeQuery(this.schema, window.location.query.substring(1))            
        } else if (window.location.hash) {
            const hash = window.location.hash.substring(1)
            queryFromURL = deserializeQuery(this.schema, hash)
            history.replaceState(null, document.title, this.currentURLBase() + "?" + hash)
        }

        if (queryFromURL) {
            this.currentSort = queryFromURL._sort
            delete queryFromURL["_sort"]
            delete queryFromURL["_auto"]
            this.currentQuery = queryFromURL
            this.currentTemplate = Object.keys(queryFromURL).slice(0)

            if (this.currentTemplate.length > 0) {
                auto = true
            }
        }

        if (history.state && Array.isArray(history.state.results)) {
            this.displayResultList(history.state.results, history.state.page || 0)
        } else if (auto) {
            this.performSearchAction(this.currentQuery, this.currentSort, this.currentTemplate)
        } else {
            this.transitionToState(PASearchProgressState.EditingQuery)
        }

        window.addEventListener("popstate", this.historyBackAction.bind(this))
        this.isFirstLoad = false
    }

    performErrorRecovery() {
        if (this.flightState === PASearchProgressState.ErrorLoadingCards) {
            this.displayResultList(this.recoveryInfo.results, this.recoveryInfo.page, false)
        } else {
            this.reloadSchema(this.recoveryInfo.overlayURLs, this.recoveryInfo.dictionaryURL).then(() => {
                if (!this.schema || !this.dictionary) {
                    return 
                }

                if (this.isFirstLoad) {
                    this.performFirstLoadStateRestoration()
                } else {
                    this.transitionToState(PASearchProgressState.EditingQuery)
                }
            })
        }

        this.recoveryInfo = null
    }
}

function PAGenericMessage(props) {
    return <div className="text-center">
        <i className="icon ion-ios-search"></i>
        <span className="h6">{props.message}</span>
    </div>
}

function PASchemaLoadErrorMessage(props) {
    const eh = (e) => {
        e.preventDefault()
        if (e.key === undefined || isActivationKey(e.key)) {
            props.action()
        }
    }

    return <div className="text-center">
        <p className="h6 mb-0">
            <i className="icon ion-ios-warning text-danger"></i>
            {Infra.strings.formatString(Infra.strings.Search.Error.SchemaLoad,
                <a href="#" onClick={(e) => eh(e, props.action)} onKeyPress={(e) => eh(e, props.action)}>
                    {Infra.strings.Search.Error.TryAgain}
                </a>
            )}
        </p>
    </div>
}

function PACardLoadErrorMessage(props) {
    const eh = (e, a) => {
        e.preventDefault()
        if (e.key === undefined || isActivationKey(e.key)) {
            a()
        }
    }

    return <div className="text-center">
        <p className="h6 mb-0">
            <i className="icon ion-ios-warning text-danger"></i>
            {Infra.strings.formatString(Infra.strings.Search.Error.CardLoad,
                <a href="#" onClick={(e) => eh(e, props.action)} onKeyPress={(e) => eh(e, props.action)}>
                    {Infra.strings.Search.Error.TryAgain}
                </a>,
                <a href="#" onClick={(e) => eh(e, props.editQueryAction)} 
                    onKeyPress={(e) => eh(e, props.editQueryAction)}>
                    {Infra.strings.Search.Error.GoBackToQueryEditor}
                </a>
            )}
        </p>
    </div>
}

function getConfig() {
    const idxFilesNodes = document.querySelectorAll("meta[name=x-panther-index-discovery]")
    const idxFiles = []
    for (let i = 0; i < idxFilesNodes.length; i++) {
        idxFiles.push(idxFilesNodes[i].content)
    }

    const dictNode = document.querySelector("meta[name=x-panther-dictionary-discovery]")

    return {indexes: idxFiles, dictionary: dictNode.content}
}

export function initializeSearch() {
    const apiType = document.querySelector("meta[name=x-panther-api]").content
    const context = new PASearchContext(apiType)
    const cfg = getConfig()

    context.reloadSchema(cfg.indexes, cfg.dictionary).then(() => {
        if (context.schema && context.dictionary) {
            context.performFirstLoadStateRestoration()
        }
    })
    console.debug("The Panther context is:", context)
    console.debug("Happy debugging!")
}
