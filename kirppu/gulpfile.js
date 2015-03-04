var gulp = require("gulp");
var gif = require("gulp-if");
var concat = require("gulp-concat");
var coffee = require("gulp-coffee");
var uglify = require("gulp-uglify");
var minify = require("gulp-minify-css");
var gutil = require("gulp-util");
var _ = require("lodash");


var pipeline = require("./pipeline");
var SRC = "static_src";
var DEST = "static/kirppu";

var jsTasks = _.map(pipeline.js, function(def, name) {
    var taskName = "js:" + name;
    gulp.task(taskName, function() {
        return gulp.src(_.map(def.source_filenames, function(n) { return SRC + "/" + n; }))
            .pipe(gif(/\.coffee$/, coffee(), gutil.noop()))
            .pipe(concat(def.output_filename))
            .pipe(uglify())
            .pipe(gulp.dest(DEST + "/js/"));
    });
    return taskName;
});

var cssTasks = _.map(pipeline.css, function(def, name) {
    var taskName = "css:" + name;
    gulp.task(taskName, function() {
        return gulp.src(_.map(def.source_filenames, function(n) { return SRC + "/" + n; }))
            .pipe(concat(def.output_filename))
            .pipe(minify())
            .pipe(gulp.dest(DEST + "/css/"));
    });
    return taskName;
});

gulp.task("pipeline", [].concat(jsTasks).concat(cssTasks), function() {

});
