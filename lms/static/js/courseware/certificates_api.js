$(document).ready(function() {
    'use strict';

    $('.generate_certs').click(function(e) {
        e.preventDefault();
        var post_url = $('.generate_certs').data('endpoint');
        $('.generate_certs').attr('disabled', true).addClass('is-disabled').attr('aria-disabled', true);
        $.ajax({
            type: 'POST',
            url: post_url,
            dataType: 'text',
            success: function() {
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('#errors-info').html(jqXHR.responseText);
                $('.generate_certs').attr('disabled', false).removeClass('is-disabled').attr('aria-disabled', false);
            }
        });
    });

    //Certificate regeneration
    $("a.request_regeneration").click( function(event) {
        var element = $(event.target);
        var do_request = confirm("Ви маєте 2 спроби на перегенерацію, пов'язану зі змінами у прізвищі, імені або по батькові. На перегенерацію через набір додаткових балів кількість спроб необмежена. Продовжити?");
        if(!do_request) {
            return false;
        }
        var post_url = $('div.cert_regeneration').data('endpoint');
        $.ajax({
            type: "POST",
            url: post_url,
            data: {'course_id': element.data("course-id")},
            success: function(data) {
                if(data.success) {
                    element.parent("div").html('<span class="regeneration_in_progress_message">Сертифікат в черзі перегенерації</span>');
                }
            },
            error: function(xhr) {
                if (xhr.status === 403) {
                    location.href = "/";
                }
            }
        });
        return false;
    });
    $("a.cert_regen_hint_toggle i").click( function(event) {
        var element = $(event.target);
        if (element.parent("a").next(".cert_regen_hint").hasClass("hidden"))
            element.parent("a").next(".cert_regen_hint").removeClass("hidden");
        else
            element.parent("a").next(".cert_regen_hint").addClass("hidden");
        return false;
    });
});
