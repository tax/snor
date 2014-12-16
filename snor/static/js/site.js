var operators = {
    eq : "Equals",
    ne : "Not equal to",
    gt : "Greater then",
    st : "Smaller then",
    startswith : "Begins with",
    not_startswith : "Does not begin with",
    "in" : "Contains",
    not_in : "Does not contain"
};

var keys = {
    "name": {
        description : "Name",
        operators : ["in","not_in","startswith","not_startswith"],
        type : "string"
    },
    "size": {
        description : "Size in MB",
        operators : ["gt","st","eq"],
        type : "int"
    },
    "peers": {
        description : "Number of peers",
        operators:["gt","st","eq"],
        type : "int"
    },
    "seeds": {
        description : "Number of seeders",
        operators:["gt","st","eq"],
        type : "int"
    }
};

function addFilter(filter){
    var source   = $("#filter-template").html();
    var template = Handlebars.compile(source); 

    filter.operatorFull = operators[filter.operator];
    filter.keyFull = keys[filter.key].description;
    $('tr.filter-form').before(template(filter));
}

$(document).ready(function(){
    $("#id_table_filters").delegate("select#id_key", "change", function(e) {
        var val = $('#id_key').val();
        $('#id_operator option').remove();
        $.each(keys[val].operators, function(index, value) {
            var html = '<option value="' + value + '">' + operators[value] + '</option>';
            $('#id_operator').append(html);
        });
    });

    $("#id_table_filters").delegate("button#id_add_filter", "click", function(e) {
        var key = $('#id_key').val();
        var op = $('#id_operator').val();
        var val = $('#id_filter_value').val();

        // Validate if value is given
        $('#id_filter_value').parent().removeClass("error");
        if(val.length == 0){
            $('#id_filter_value').parent().addClass("error");
            return;        
        }
        
        // Validate if value is numeric when datatype is int
        if(keys[key].type == "int" && !/^\d+$/.test(val)){
            $('#id_filter_value').parent().addClass("error");
            $('#id_filter_value').val("");
            $('#id_filter_value').attr("placeholder","Needs to be a number");      
            return;
        }

        addFilter({key:key, value:val, operator:op});
        $('#id_filter_value').val("");
        $('#id_filter_value').attr("placeholder","Value...");

    });
    $("#id_table_filters").delegate("button.action_remove_filter", "click", function(e) {
        $(this).parents('tr').remove();
    });
});