/**
 *  ViewModel for the new-homework template, using Knockout.js
 */

function ViewModel() {
    const self = this;

    self.loading = ko.observable(false);

    self.formErrorsVisible = ko.observable(false);
    self.formErrors = ko.observableArray();

    self.changeFormErrorsVisible = function (visibility) {
        self.formErrorsVisible(visibility);
    };

    self.course = {
        name: ko.observable(),
        id: ko.observable()
    };

    self.previous_scales = {
        name: ko.observable(),
        id: ko.observable(),
        criteria: ko.observable()
    };


    self.type_scales = {
        name: ko.observable(),
        id: ko.observable(),
        description: ko.observable()
    };


    self.select = new Select();
    self.homework = {
        description: ko.observable(""),
        organizer: ko.observable(),
        course: ko.observable(),
        previous_scales: ko.observable(),
        type_scales: ko.observable(),
        revision: ko.observable(3),
        title: ko.observable(""),
        video: ko.observable(""),
        date_upload: ko.observable(""),
        date_evaluation: ko.observable(""),
        homework_to_evaluate: ko.observable()
    };

    self.chosen_scale = ko.observable("");
    self.homework.type_scales.subscribe(function () {
        let val = self.homework ? self.homework.type_scales() : null;
        self.chosen_scale(val ? self.select.type_scales.filter(d=>d.id === val)[0].description : "");

    });

    self.assignGroups = new AssignGroups();


    self.criteria = ko.observableArray(ko.utils.arrayMap([""], function(item) {
            return { name: ko.observable(item),description: ko.observable(item) };
        }));
    self.removeCriterion = function(child) {
            if (self.criteria().length <= 1) {
                vm.formErrors.removeAll();
                vm.changeFormErrorsVisible(true);
                vm.formErrors.push("Debes tener al menos un criterio");
                $('html,body').animate({
                scrollTop: $("#top-form-head-line").offset().top},
                'slow');
            }else {
             self.criteria.remove(child);
            }
        };
    self.addCriterion = function () {
            self.criteria.push({ name: ko.observable(""),description: ko.observable("") });
        };


    self.submitNewHomeworkForm = function () {
        const fd = new FormData();
        fd.append("description", self.homework.description());
        fd.append("organizer", self.homework.organizer());
        fd.append("course", self.homework.course());
        fd.append("revision", parseInt(self.homework.revision()));
        fd.append("title", self.homework.title());
        fd.append("video", self.homework.video());
        let criteria_arr = [];
        for(let c of self.criteria()){
            criteria_arr.push({name:c.name(),description: c.description()});
        }
        fd.append("scale",JSON.stringify({criteria: criteria_arr, scale: self.homework.type_scales()}));
        if (self.homework.homework_to_evaluate()) fd.append("homework_to_evaluate", self.homework.homework_to_evaluate());
        fd.append("date_upload", self.homework.date_upload());
        fd.append("date_evaluation", self.homework.date_evaluation());
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
        return $.ajax("/teacher/new-homework-form/", {
            data: fd,
            type: "post",
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.success) {
                    self.assignGroups.currentHomework(response.id);
                    $("#assign-group-form-submit").click();
                } else {
                    $(".loader").fadeOut("slow");
                    self.formErrors.removeAll();
                    self.changeFormErrorsVisible(true);
                    for (let i = 0; i < response.errors.length; i++) {
                        self.formErrors.push(response.errors[i]);
                    }
                    $('html,body').animate({
                            scrollTop: $("#top-form-head-line").offset().top
                        },
                        'slow');
                }
            }
        });
    };

    self.submitForms = function () {
        if ($("#groups-form").valid() && $("#new-homework-form").valid()) {
            self.loading(true);
            $(".loader").fadeIn("slow");
            $("#new-homework-form-submit").click();
        }
    };

    self.onSelectChangeValue = function (value) {
        $.when($.ajax("/teacher/download-course/" + value + "/")).done(
            function (result) {
                self.assignGroups.students.removeAll();
                self.course.name(result.course.name);
                self.course.id(result.course.id);
                for (i = 0; i < result.students.length; i++) {
                    const a = result.students[i];
                    self.assignGroups.students.push(new Student(parseInt(a.id), a.last_name, a.first_name));
                }
                self.assignGroups.hasCourse(true);
            }
        );
    };

    // Subscribe function for change in select
    self.homework.course.subscribe(function () {
        self.onSelectChangeValue(self.homework.course());
    });

    self.homework.previous_scales.subscribe(function () {
        const val = self.homework.previous_scales();
        if(val){
            console.log("WIII",val);
        }else{
            console.log("no value");
        }
    });

    self.submitGroupsForm = function () {
        const groups = {};
        for (let i = 0; i < self.assignGroups.students().length; i++) {
            student = self.assignGroups.students()[i];
            try {
                groups[student.group().toString()].push(student.id());
            } catch (err) {
                console.log(err);
                groups[student.group().toString()] = [student.id()];
            }
        }
        $.when(self.assignGroups.submitGroups(groups, "/teacher/assign-group-form/")).done(
            function (result) {
                $(".loader").fadeOut("slow");
                alert("Tarea creada exitosamente.");
                window.location = '/teacher/';
            }
        );
    }
}

var vm = new ViewModel();