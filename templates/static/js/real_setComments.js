/**
 * Created by garou6666 on 7/26/16.
 */


function setComments(d) {

    var url = full_analysis.flat_tree[d.nid].url;
    var ip = full_analysis.flat_tree[d.nid].ip;

    //Get comment for selected node
    $.getJSON('/api/v1/comments/?format=json&task_id=' + task_id + '&node='+url, function(response) {

        var objects = response.objects;
        var size = Object.keys(objects).length;

        // SHow comment tab with the amount of comments for selected node
        $('#comments-tab-name').css('visibility', 'visible');
        $('#comments-tab').html(size+' Node Comments');
        $('.comments-list').empty();

        for (var key in objects) {
            
            $('#comments-list').append("" +
                "<li>" +
                    "<div class='comment-box'>" +
                        "<div class='comment-head'>" +
                            "<h6 class='comment-name by-author'>" + objects[key]['user']['username'] + "</h6>" +
                            "<span><h6>" + new Date(objects[key]['created_on']).toLocaleString() + "</h6></span>" +
                        "</div>" +
                        "<div class='comment-content'  style='word-wrap: break-word'>" + objects[key]['text'] +
                        "</div>" +
                    "</div>" +
                "</li>");
        }

    });

    // Comment titles with currently selected node and IP
    $('#comment-title').html(url);
    $('#comment-node').val(url);
    $('#comment-ip-title').html(ip);






}