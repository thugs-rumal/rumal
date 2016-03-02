function setTree() {
    var wrap_height = $("#wrap")
        .outerHeight(true),
        wrap_width = $("#wrap")
        .outerWidth(true),
        margin = {
            top: 50,
            right: 50,
            bottom: 50,
            left: 50
        },
        width = wrap_width,
        height = wrap_height;
        console.log(height)
    var i = 0,
        duration = 750,
        root;
    var tree = d3.layout.tree()
        .size([height - margin.top, width - margin.left - margin.right]);
    /*used for manual zooming*/
    var diagonal = d3.svg.diagonal()
        .projection(function(d) {
            return [d.y, d.x];
        });
    var svg = d3.select("#wrap")
        .append("div")
        .attr("class", "tree")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g");
    if(navigator.userAgent.indexOf('Chrome')>0){
        d3.select('.tree svg').style("padding-left",margin.left);
    } else{
        d3.select('.tree svg').attr("transform", "translate(" + margin.left + ",0)");
    }

    /* for pan and zoom*/
    var threat_path_elements = [];

    function setD3Graph(flare) {
        root = flare;
        root.x0 = height / 2;
        root.y0 = 0;

        function collapse(d) {
            if (d.children) {
                d._children = d.children;
                d._children.forEach(collapse);
                d.children = null;
            }
        }

        function higlight_threat_path(node) {
            var ancestors = [];
            var parent = node;
            while (!_.isUndefined(parent)) {
                ancestors.push(parent);
                /*parent.threat_path = 1;*/
                if (parent.parent === null) {
                    break;
                }
                parent = parent.parent;
            }
            $.merge(threat_path_elements, ancestors);
            /*ancestors.forEach(collapse);*/
            var matchedLinks = [];
            var x = svg.selectAll("path.link")
                .filter(function(d, i) {
                    return _.any(ancestors, function(p) {
                        return p === d.target;
                    });
                })
                .attr("stroke", "#F44336");
        }
        /*  root.children.forEach(collapse);*/
        update(root);
        /*  collapse(root);*/
        threat_nodes = svg.selectAll("g.node")
            .filter(function(d, i) {
                return d.threat_path == 1;
            })
            .each(function(d, i) {
                higlight_threat_path(d);
            });
        svg.selectAll("g.node")
            .each(function(d, i) {
                if ($.inArray(d, threat_path_elements) === -1 && d.children) {
                    collapse(d);
                    update(d);
                }
            });
    }
    setD3Graph(full_analysis["nested_tree"]);
    d3.select(self.frameElement)
        .style("height", "800px");

    function update(source) {
        /* Compute the new tree layout.*/
        var nodes = tree.nodes(root)
            .reverse(),
            links = tree.links(nodes);
        /* Normalize for fixed-depth.*/
        /*nodes.forEach(function(d) { d.y = d.depth * 180; });*/
        /* Update the nodes…*/
        var node = svg.selectAll("g.node")
            .data(nodes, function(d) {
                return d.id || (d.id = ++i);
            });
        /* Enter any new nodes at the parent's previous position.*/
        var nodeEnter = node.enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", function(d) {
                return "translate(" + source.y0 + "," + source.x0 + ")";
            })
            .on("dblclick", dblclick)
            .on("click", click);
        nodeEnter.append("circle")
            .attr("r", 1e-6)
            .style("fill", function(d) {
                return d._children ? "lightsteelblue" : "#fff";
            });
        nodeEnter.append("text")
            .attr("x", function(d) {
                return d.children || d._children ? -10 : 10;
            })
            .attr("dy", ".35em")
            .attr("text-anchor", function(d) {
                return d.children || d._children ? "end" : "start";
            })
            .text(function(d) {
                return d.name;
            })
            .style("fill-opacity", 1e-6);
        /* Transition nodes to their new position.*/
        var nodeUpdate = node.transition()
            .duration(duration)
            .attr("transform", function(d) {
                return "translate(" + d.y + "," + d.x + ")";
            });
        nodeUpdate.select("circle")
            .attr("r", 4.5)
            .style("fill", function(d) {
                return d._children ? "lightsteelblue" : "#fff";
            });
        nodeUpdate.select("text")
            .style("fill-opacity", 1);
        /* Transition exiting nodes to the parent's new position.*/
        var nodeExit = node.exit()
            .transition()
            .duration(duration)
            .attr("transform", function(d) {
                return "translate(" + source.y + "," + source.x + ")";
            })
            .remove();
        nodeExit.select("circle")
            .attr("r", 1e-6);
        nodeExit.select("text")
            .style("fill-opacity", 1e-6);
        /* Update the links…*/
        var link = svg.selectAll("path.link")
            .data(links, function(d) {
                return d.target.id;
            });
        /* Enter any new links at the parent's previous position.*/
        link.enter()
            .insert("path", "g")
            .attr("class", "link")
            .attr("stroke", "#4CAF50")
            .attr("d", function(d) {
                var o = {
                    x: source.x0,
                    y: source.y0
                };
                return diagonal({
                    source: o,
                    target: o
                });
            });
        /* Transition links to their new position.*/
        link.transition()
            .duration(duration)
            .attr("d", diagonal);
        /* Transition exiting nodes to the parent's new position.*/
        link.exit()
            .transition()
            .duration(duration)
            .attr("d", function(d) {
                var o = {
                    x: source.x,
                    y: source.y
                };
                return diagonal({
                    source: o,
                    target: o
                });
            })
            .remove();
        /* Stash the old positions for transition.*/
        nodes.forEach(function(d) {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }
    /* Toggle children on click.*/
    function click(d) {
        setPanels(d.nid);
    }

    function dblclick(d) {
        if ($.inArray(d, threat_path_elements) === -1) {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else {
                d.children = d._children;
                d._children = null;
            }
            update(d);
        }
    }
    var tree_zoom = d3.behavior.zoom()
        .scaleExtent([1, 4])
        .on("zoom", tree_zoomed);
    d3.select(".tree svg")
        .call(tree_zoom)
        .on("dblclick.zoom", null);

    function tree_zoomed() {
        d3.select(".tree svg g")
            .attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    }
}