function pagination_hide() {
    var vars = {};
    var x = document.location.search.substring(1).split('&amp');
    for (var i in x) {
        var z = x[i].split('=', 2);
        vars[z[0]] = unescape(z[1]);
    }

    if (vars['page'] <= 1){
        hidden_nodes = document.getElementsByClassName("hide_firstpage");
        for (i = 0; i < hidden_nodes.length; i++) {
            hidden_nodes[i].style.visibility = "hidden";
        }
    }

    if (vars['page'] == vars['topage']){
        hidden_nodes = document.getElementsByClassName("show_lastpage");
        for (i = 0; i < hidden_nodes.length; i++) {
            hidden_nodes[i].style.display = "block";
        }
    }

    if (vars['page'] == 1){
        hidden_nodes = document.getElementsByClassName("show_firstpage");
        for (i = 0; i < hidden_nodes.length; i++) {
            hidden_nodes[i].style.display = "block";
        }
    }
}