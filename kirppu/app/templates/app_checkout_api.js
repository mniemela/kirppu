(function() {
    var Api = {};
{% for name, f in funcs.iteritems %}

Api['{{ name }}'] = function(params, onSuccess, onError) {
    return $.ajax({
        type: '{{ f.method }}',
        url:  '{% url f.view %}',
        data: params
    });
};

{% endfor %}
    window.Api = Api;
}).call(this);
