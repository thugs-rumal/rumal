function setPanels(nid) {
    /*set basic info panel*/
    var $basic_table = $("<table>").addClass("table table-striped table-hover");
    var $row = $("<tr>").append($("<td>").html("url")).append($("<td>").html(full_analysis.flat_tree[nid].url));
    $basic_table.append($row);
    var $row = $("<tr>").append($("<td>").html("ip")).append($("<td>").html(full_analysis.flat_tree[nid].ip));
    $basic_table.append($row);
    if (full_analysis.flat_tree[nid].certificate) {
        var $row = $("<tr>").append($("<td>").html("certificate")).append($("<td>").html(full_analysis.flat_tree[nid].certificate));
        $basic_table.append($row);
    }
    var $row = $("<tr>").append($("<td>").html("thug verison")).append($("<td>").html(full_analysis.thug.version));
    $basic_table.append($row);
    if (full_analysis.thug.options.proxy) {
        var $row = $("<tr>").append($("<td>").html("proxy")).append($("<td>").html(full_analysis.thug.options.proxy));
        $basic_table.append($row);
    }
    $("#sidebar > div:nth-child(1) > div").html($("<b>").html("Basic Info")).append($basic_table);
    /*set samples panel*/
    var samples = full_analysis.flat_tree[nid].samples;
    var $samples_table = $("<table>").addClass("table table-striped table-hover").append($("<tr>").append($("<th>").html("type")).append($("<th>").html("md5")).append($("<th>").html("actions")));
    for (var i in samples) {
        var $row = $("<tr>").append($("<td>").html(samples[i].type)).append($("<td>").html(samples[i].md5)).append($("<td>").append($("<a>").html("save")).append(" | ").append($("<a>").html("view")));
        $samples_table.append($row);
    }
    $("#sidebar > div:nth-child(2) > div").html($("<b>").html("Samples")).append($samples_table);
    /*set codes panel*/
    var codes = full_analysis.codes;
    var $codes_table = $("<table>").addClass("table table-striped table-hover").append($("<tr>").append($("<th>").html("language")).append($("<th>").html("method")).append($("<th>").html("actions")));
    for (var i in codes) {
        var $row = $("<tr>").append($("<td>").html(codes[i].language)).append($("<td>").html(codes[i].method)).append($("<td>").append($("<a>").html("view").data("idx", i)));
        $codes_table.append($row);
    }
    $("#sidebar > div:nth-child(3) > div").html($("<b>").html("Codes")).append($codes_table);
    $("#sidebar > div:nth-child(3) > div a").click(function() {
        var idx = +$(this).data();
        var $codes_table = $("<table>").addClass("table table-striped table-bordered").append($("<tr>").append($("<td>").html("language")).append($("<td>").html(codes[i].language))).append($("<tr>").append($("<td>").html("method")).append($("<td>").html(codes[i].method))).append($("<tr>").append($("<td>").html("relationship")).append($("<td>").html(codes[i].relationship)));
        var snippet = $("<pre>").addClass("prettyprint linenums").html(codes[i].snippet);
        $("#myModal\n                    .modal - title ").html("key");
        $("#myModal\n                        .modal - body ").html($codes_table).append(snippet);
        $("#myModal").modal("show");
        prettyPrint();
    });
    /*set plugins panel*/
    var plugins_rumal_list = [ "virustotal", "honeyagent", "androguard", "peepdf", "maec11" ];
    var plugins_rumal = {};
    for (var i in plugins_rumal_list.sort()) {
        var key = plugins_rumal_list[i];
        plugins_rumal[key] = full_analysis[key];
    }
    var plugins_thug = [];
    for (var key in full_analysis.flat_tree[nid]) {
        if (key.indexOf("Plugin") > -1) {
            key = key.split("Plugin").join(" Plugin");
            plugins_thug[key] = full_analysis.flat_tree[nid][key];
        }
    }
    var $plugins_table = $("<table>").addClass("table table-striped table-hover").append($("<tr>").append($("<th>").html("Thug Plugins")));
    for (var i in plugins_rumal) {
        var $row = $("<tr>").append($("<td>").html(i)).append($("<td>").html($("<a>").data("origin", "thug").data("key", i).html("view")));
        $plugins_table.append($row);
    }
    $plugins_table.append($("<tr>").append($("<th>").html("Rumal Plugins")));
    for (var i in plugins_thug) {
        var $row = $("<tr>").append($("<td>").html(i)).append($("<td>").html($("<a>").data("origin", "rumal").data("nid", nid).data("key", i).html("view")));
        $plugins_table.append($row);
    }
    $("#sidebar > div:nth-child(4) > div").html($("<b>").html("Plugins")).append($plugins_table);
    $("#sidebar > div:nth-child(4) > div a").click(function() {
        var title = null;
        var body = null;
        if ($(this).data("origin") === "thug") {
            title = $(this).data("key");
            body = JsonHuman.format(full_analysis[$(this).data("key")]);
        } else {
            var key = $(this).data("key").replace(" ", "");
            title = key;
            body = JsonHuman.format(full_analysis.flat_tree[nid][key]);
        }
        $("#myModal\n                                .modal - title ").html(key);
        $("#myModal\n                                    .modal - body ").html(body);
        $("#myModal").modal("show");
    });
    /*set threats panel*/
    var threats = full_analysis.flat_tree[nid].threats;
    var $threats_table = $("<table>").addClass("table table-striped table-hover");
    for (var i in threats) {
        var threat = threats[i];
        var $row = $("<tr>").append($("<td>").html(threat.type)).append($("<td>").append($("<a>").attr("href", "#").data("nid", nid).html("view")));
        $threats_table.append($row);
    }
    $("div\n                                    .panel: nth - child(7) > div: nth - child(2)\n                                    ").html($threats_table);
    $("div\n                                        .panel: nth - child(7) > div: nth - child(2) a ").click(function() {
        var node = JsonHuman.format(threats[0].details);
        $("#myModal").modal("show");
        $("#myModal\n                                                    .modal - title ").html(threats[0].type);
        $("#myModal\n                                                        .modal - body ").html($(node));
    });
    /*reset scroll*/
    $("#first").mouseleave(function() {
        $(this).scrollTop(0);
    });
    $("#samples")
        .mouseleave(function() {
            $(this)
                .scrollTop(0);
        });
    $("#codes")
        .mouseleave(function() {
            $(this)
                .scrollTop(0);
        });
    $("#plugins")
        .mouseleave(function() {
            $(this)
                .scrollTop(0);
        });
}