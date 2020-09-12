
function _openGutterAction(event) {
    console.debug("_openGutterAction trigger!")
    const h = document.querySelector(".gutter-menu-host")
    const animationTarget = h.querySelector(".gutter-menu-main")

    if (!h.classList.contains("opened")) {
        h.classList.add("opened")
        console.debug("starting anim")
        animationTarget.classList.add("animation-state-start")
        requestAnimationFrame(() => {
            animationTarget.classList.remove("animation-state-start")
        })
    } else {
        animationTarget.classList.add("animation-state-start")
        animationTarget.addEventListener("transitionend", () => {
            h.classList.remove("opened")
        }, {once: true})
    }
}

function _dismissGutterAction(event) {
    const host = document.querySelector(".gutter-menu-host")
    if (event.currentTarget === event.target && host.classList.contains("opened")) {
        _openGutterAction(event)
    }
}

export function injectIntoPage() {
    const triggers = document.querySelectorAll("#open-gutter")
    for (let i = 0; i < triggers.length; i++) {
        const button = triggers[i]
        button.addEventListener("click", _openGutterAction, {passive: true})
    }

    const host = document.querySelector(".gutter-menu-host")
    host.addEventListener("click", _dismissGutterAction, {passive: true})
}