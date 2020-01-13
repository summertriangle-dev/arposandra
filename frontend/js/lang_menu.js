import React from "react"
import ReactDOM from "react-dom"

class _LanguageMenu extends React.Component {
    
}


////////////////////////////////////////////////////

let isLangmenuMounted = false

export function initLanguageMenu() {
    document.querySelector("#bind-langmenu-toggle").addEventListener("click", () => {
        if (isLangmenuMounted) {
            ReactDOM.unmountComponentAtNode(document.querySelector("#bind-gutter"))
            isLangmenuMounted = false
        } else {
            mountLangmenu()
            isLangmenuMounted = true
        }
    })
}


function mountLangmenu() {

}