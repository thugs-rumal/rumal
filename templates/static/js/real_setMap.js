function setMap(tooltip) {
    var height = $("#wrap")
        .outerHeight(true),
        width = $("#wrap")
        .outerWidth(true);
    var projection = d3.geo.equirectangular()
        .scale(120)
        .translate([width / 2, height / 2]),
        path = d3.geo.path()
        .projection(projection);
    var map_div = d3.select("#wrap")
        .append("div")
        .attr("class", "map"),
        map_svg = map_div.append("svg")
        .attr("width", width)
        .attr("height", height),
        map_g = map_svg.append("g");
    d3.json("/static/js/world-110m2.json", function(error, topology) {
        map_g.selectAll("path")
            .data(topojson.object(topology, topology.objects.countries)
                .geometries)
            .enter()
            .append("path")
            .attr("d", path);
        map_g.selectAll("circle")
            .data(loadMapPoints())
            .enter()
            .append("circle")
            .attr("cx", function(d) {
                return projection([d["Longitude"], d["Latitude"]])[0];
            })
            .attr("cy", function(d) {
                return projection([d["Longitude"], d["Latitude"]])[1];
            })
            .attr("r", 2)
            .style("fill", "red")
            .on("mouseover", function(d) {
                tooltip.transition()
                    .duration(100)
                    .style("opacity", .9);
                tooltip.html(d["City"])
                    .style("left", d3.event.pageX + 20 + "px")
                    .style("top", d3.event.pageY + "px");
            })
            .on("mouseout", function(d) {
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });
    });
    var map_zoom = d3.behavior.zoom()
        .scaleExtent([1, 4])
        .on("zoom", map_zoomed);
    d3.select(".map svg")
        .call(map_zoom);

    function map_zoomed() {
        d3.select(".map svg g")
            .attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    }
}

function loadMapPoints() {
    var points = [];
    for (var i in full_analysis["flat_tree"]) {
        var iflat_tree = full_analysis['flat_tree'][i];
        if ('GeoPlugin' in iflat_tree && 'city' in iflat_tree['GeoPlugin'] && "City" in iflat_tree["GeoPlugin"]["city"]) {
            var city = iflat_tree["GeoPlugin"]["city"];
            points.push(city);
        }
    }
    return points;
}

