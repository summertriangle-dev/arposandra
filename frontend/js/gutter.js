const GUTTER_MIN_OFFSET_FROM_BOTTOM = 30

const adjustGutterScrollable = (() => {
    const mem = {scrollEnabled: true, chromeSize: undefined, maxHeight: false}

    return (gutter) => {
        if (window.innerWidth >= 1560 && mem.chromeSize === undefined) {
            mem.chromeSize = gutter.getBoundingClientRect().top + GUTTER_MIN_OFFSET_FROM_BOTTOM
        }

        if (window.innerWidth >= 1560) {
            gutter.style.maxHeight = (window.innerHeight - mem.chromeSize) + "px"
            gutter.style.overflowY = "scroll"
            mem.scrollEnabled = true
            mem.maxHeight = true
        } else {
            if (mem.maxHeight) {
                gutter.style.maxHeight = null
                mem.maxHeight = false
            }
        }

        if (!mem.scrollEnabled) {
            if (gutter.clientHeight < gutter.scrollHeight) {
                gutter.style.overflowY = "scroll"
                mem.scrollEnabled = true
            }
        } else {
            if (gutter.clientHeight >= gutter.scrollHeight) {
                gutter.style.overflowY = "hidden"
                mem.scrollEnabled = false
            }
        }
    }
})()

function _openGutterAction() {
    console.debug("_openGutterAction trigger!")
    const host = document.querySelector(".gutter-host")
    const animationTarget = host.querySelector(".gutter")

    if (!host.classList.contains("opened")) {
        host.classList.add("opened")
        console.debug("starting anim")
        animationTarget.classList.add("animation-state-start")
        requestAnimationFrame(() => {
            animationTarget.classList.remove("animation-state-start")
        })
    } else {
        animationTarget.classList.add("animation-state-start")
        animationTarget.addEventListener("transitionend", () => {
            host.classList.remove("opened")
        }, {once: true})
    }

    adjustGutterScrollable(animationTarget)
}

function _dismissGutterAction(event) {
    const host = document.querySelector(".gutter-host")
    if (event.currentTarget === event.target && host.classList.contains("opened")) {
        _openGutterAction()
    }
}

export function injectIntoPage() {
    const triggers = document.querySelectorAll(".open-gutter")
    for (let i = 0; i < triggers.length; i++) {
        const button = triggers[i]
        button.addEventListener("click", _openGutterAction, {passive: true})
    }

    const host = document.querySelector(".gutter-host")
    if (host) {
        host.addEventListener("click", _dismissGutterAction, {passive: true})
    }

    const gutterScrollable = document.querySelector(".gutter")
    if (gutterScrollable) {
        window.addEventListener("resize", () => adjustGutterScrollable(gutterScrollable), {passive: true})
        adjustGutterScrollable(gutterScrollable)
    }
}
