function openSubmenu(e) {
    e.preventDefault()
    const parent = e.currentTarget.parentNode
    const submenu = parent.querySelector(".nav-submenu")
    if (submenu.classList.contains("open")) {
        submenu.classList.remove("open")
        return
    }

    closeAllSubmenus()
    submenu.classList.add("open")
    submenu.classList.add("animation-state-start")
    requestAnimationFrame(() => requestAnimationFrame(() => submenu.classList.remove("animation-state-start")))
    createDismissTarget()
}

function closeAllSubmenus() {
    const onTransitionEnd = (e) => {
        e.target.classList.remove("open")
        e.target.classList.remove("animate-out")
    }

    const others = document.querySelectorAll(".nav-submenu.open")
    for (let i = 0; i < others.length; i++) {
        others[i].classList.add("animate-out")
        others[i].addEventListener("transitionend", onTransitionEnd, {once: true})
    }

    const dismissTarget = document.querySelector(".nav-dismiss-target")
    if (dismissTarget) {
        dismissTarget.parentNode.removeChild(dismissTarget)
    }
}

function createDismissTarget() {
    const e = document.createElement("div")
    e.className = "nav-dismiss-target"
    e.onclick = closeAllSubmenus
    e.style.position = "absolute"
    e.style.top = 0
    e.style.left = 0
    e.style.right = 0
    e.style.bottom = 0
    e.style.zIndex = 40

    document.body.appendChild(e)
}

export function injectIntoPage() {
    const triggers = document.querySelectorAll(".nav-submenu-opener")
    const mousedownEvent = (e) => {
        if (e.button == 0) openSubmenu(e)
    }
    const keydownEvent = (e) => {
        if (e.keyCode == 0x0d || e.keyCode == 0x20) openSubmenu(e)
    }
    const clickEvent = (e) => e.preventDefault()
    for (let i = 0; i < triggers.length; i++) {
        const button = triggers[i]
        button.addEventListener("mousedown", mousedownEvent, {passive: false})
        button.addEventListener("touchstart", openSubmenu, {passive: false})
        button.addEventListener("click", clickEvent, {passive: false})
        button.addEventListener("keydown", keydownEvent, {passive: false})
        button.href = "#"
    }
}
