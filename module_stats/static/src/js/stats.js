odoo.define('module_stats.fetch', function(require) {
    "use strict";
    var core = require('web.core');
    var qweb = core.qweb;
    var ajax = require('web.ajax');
    var fields = [];
    var modules = {};
    var fetchURL = '/module_stats/json';
    var searchPattern;
    var moduleCounts; // needed for redraw
    var workbook;

    function renderStats() {
        /* remove containers */
        $("#ModStats").remove();

        if ( _.size( modules ) > 0 ) {
            /* set form state */
            $("#inputPath").removeClass("is-invalid");
            $("#toShowChecks input").prop("checked", true);
            $("#btnRedraw").enable();
            $("#btnDownload").removeClass("d-none");

            /* init count objects */
            moduleCounts = {}
            var globalCounts = {
                "modules": _.size(modules),
                "dependencies": 0,
                "menus": 0,
                "reports": 0,
                "views": 0,
                "models": 0,
            };
            /* init sheets object with headers */
            var sheetsData = {
                "dependencies": [["module", "dependecy", "path"]],
                "records": [["module", "model", "name", "typw", "extended"]],
                "models": [[
                    "module", "name", "classname", "extended",
                    "inherits", "fields", "records",
                ]],
            }
            
            /* fill global counts objects and sheetData */
            let globalKeys = ['dependencies', 'menus', 'reports', 'views', 'models']
            for (let name in modules) {
                let mod = modules[name];
                moduleCounts[name] = {};
                for (let field in mod) {
                    let size = _.size( mod[field] );
                    moduleCounts[name][field] = size;

                    if ( _.contains(globalKeys, field) ) {
                        globalCounts[field] += size;
                    }

                    fillSheetsData(sheetsData, mod, field);
                }
            }

            /* init and fill workbook */
            workbook = XLSX.utils.book_new();
            for (const name in sheetsData) {
                let sheet = XLSX.utils.aoa_to_sheet(sheetsData[name]);
                XLSX.utils.book_append_sheet(workbook, sheet, name);
            }

            /* render main stats container with global stats panel */
            $( qweb.render('module_stats.stats_div', {
                'stats': globalCounts,
                'pattern': searchPattern,
            }) ).appendTo( $("main .container") );
            /* set event listeners */
            $("#toggleGlobals").on("click", function() {
                $(".transitive").toggleClass("opened");
            });

            /* render lists */
            renderLists();
        } else {
            $("#inputPath").addClass("is-invalid");
            $("#btnRedraw").enable(false);
            $("#btnDownload").addClass("d-none");
        }
    }

    function fillSheetsData(sheetsData, module, field) {
        var keys = ['name', 'type', 'is_extended'];
        var path = module.path.slice(0, -1 * module.length);
        if (field == 'dependencies') {
            module[field].forEach(function(dep) {
                let valsOrdered = [module, dep, path];
                sheetsData.dependencies.push(valsOrdered);
            });
        } else if (_.contains(['menus', 'reports', 'views'], field)) {
            module[field].forEach(function(val) {
                let valsOrdered = [module, field.slice(0, -1)].concat(
                    _.map(keys, function(key) {
                        if (key == 'is_extended') {
                            return String(val[key]).toUpperCase();
                        } else {
                            return val[key];
                        }
                    })
                );
                sheetsData.records.push(valsOrdered);
            });
        } else if (field == 'models') {
            keys = ['classname', 'is_extended', 'inherits', 'fields', 'records'];
            for (const name in module[field]) {
                let val = module[field][name];
                let valsOrdered = [module, name].concat(
                    _.map(keys, function(key) {
                        if (key == 'is_extended') {
                            return String(val[key]).toUpperCase();
                        } else if ( _.contains(['inherits', 'fields'], key) ) {
                            return val[key].join(',');
                        } else {
                            return val[key];
                        }
                    })
                );
                sheetsData.models.push(valsOrdered);
            }
        }
    }

    function renderLists() {
        /* save checkbox states */
        fields = $("#ModStatsForm :checkbox").map(function () {
            if ( this.checked ) { return this.name; }
        }).get();

        /* remove container */
        $("#ModStatsLists").remove();

        /* render template */
        $(qweb.render(
            'module_stats.list_group',
            {
                'modules': modules,
                'fields': fields,
                'counts': moduleCounts,
            },
        )).appendTo("#ModStats");

        /* add event listeners */
        $("a.list-group-item-action").on("click", setContentWidth );
    }

    function setContentWidth() {
        let $tabContent = $(`#${this.dataset.moduleName}_content`);
        if ( this.href.split('_').pop() == 'models' ) {
            $tabContent.removeClass("col-8").addClass("col-12");
        } else {
            $tabContent.removeClass("col-12").addClass("col-8");
        }
    }

    function postRequest() {
        /* clear path input and hide spinner */
        $("#inputPath").val(null);
        $("#spinner").addClass("d-none").removeClass("d-flex");

        /* disable checkboxes 'models' and 'fields' if unchecked */
        $("#checkModels, #checkFields").each( function () {
            this.checked || $(this).enable(false);
        });
    }

    $(function() {
        /* load template file */
        qweb.add_template('/module_stats/static/src/xml/snippets.xml');

        /* set shower checkboxes to checked */
        $("#toShowChecks input").prop("checked", true);

        $("#inputPath").on("change", function () {
            $("#checkModels").enable();
        });

        $("#checkModels").on("change", function () {
            if (this.checked) {
                $("#checkFields").enable();
            } else {
                $("#checkFields").enable(false).prop("checked", false);
            }
        });

        $("#btnRedraw").on("click", renderLists);
        $("#btnDownload").on("click", function() {
            XLSX.writeFile(workbook, 'odoo_module_stats.xlsx')
        });

        $("#ModStatsForm").on("submit", function(ev) {
            /* prevent form submit and reload */
            ev.preventDefault();
            ev.stopPropagation();

            /* show spinner and read search pattern */
            $("#spinner").addClass("d-flex").removeClass("d-none");
            searchPattern = $("#inputPath").val();

            /* fetch data */
            $.ajax({
                url: fetchURL,
                type: "POST",
                contentType: "application/json; charset=utf-8",
                dataType: 'json',
                data: JSON.stringify({
                    'jsonrpc': "2.0", 'method': "call",
                    'params': {
                        'pattern': searchPattern,
                        'get_models': $("#checkModels").prop('checked'),
                        'get_fields': $("#checkFields").prop('checked'),
                    },
                }),
                success: function (data) {
                    /* save module object and render stats */
                    modules = data.result;
                    renderStats();
                    postRequest();
                },
                error: function (data) {
                    console.error("ERROR ", data);
                    postRequest();
                },
            });
        });
    });
});
