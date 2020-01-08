import React from "react"
import ReactDOM from "react-dom"
import Infra from "./infra"

class SearchForm extends React.Component {
    render() {
        return <div className="container">
                <div className="kars-stack">
                    <div class="kars-stack-header">Search...</div>
                    <div class="field kars-stack-member">
                        <p class="control has-icons-left">
                        <input class="input" type="text" placeholder="Search..." />
                        <span class="icon is-small is-left"><i class="ion-ios-search"></i></span>
                        </p>
                    </div>
                    <div class="kars-stack-header">Attribute</div>
                    <div class="kars-stack-member">
                        <span class="tag"><i class="ion-ios-close"></i></span>
                        <span class="tag is-info">Smile</span>
                        <span class="tag is-info">Pure</span>
                        <span class="tag is-info">Cool</span>
                        <span class="tag is-info">Active</span>
                        <span class="tag is-info">Natural</span>
                        <span class="tag is-info">Elegant</span>
                    </div>
                    <div class="kars-stack-header">Role</div>
                    <div class="kars-stack-member">Filters</div>
                    <div class="kars-stack-header">Affiliation</div>
                    <div class="kars-stack-member">Filters</div>
                    <div class="kars-stack-member">Filters</div>
                </div>
        </div>
    }
}

let isSearchMounted = false;
export function search_init() {
    document.querySelector("#bind-search-toggle").addEventListener("click", () => {
        const theNode = document.querySelector("#contains-search-form")
        if (isSearchMounted) {
            ReactDOM.unmountComponentAtNode(theNode)
        } else {
            ReactDOM.render(<SearchForm />, theNode)
        }
        isSearchMounted = !isSearchMounted
    })
}