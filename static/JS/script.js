function ajustarLargura() {
    var larguraTela = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth

    for (var i = 1; i <= vagas.length; i++) {
        var container = document.getElementById("vagaContainer" + i)

        if (larguraTela >= 768 && larguraTela < 992) {
            container.classList.remove("w-50")
            container.classList.add("w-100")
        } else if (larguraTela >= 992 && larguraTela < 1200) {
            container.classList.remove("w-100")
            container.classList.add("w-50")
        }
    }
}

ajustarLargura()
window.addEventListener('resize', ajustarLargura)
