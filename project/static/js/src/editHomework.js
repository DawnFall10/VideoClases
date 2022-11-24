/*
 *  ViewModel for editHomework template
 */

function ViewModel() {
    var self = this;
    self.editGroup = new EditGroup();
    self.select = new Select();
    self.editHomeworkBool = ko.observable(false);
    self.id = ko.observable();
    self.formErrorsVisible = ko.observable(false);
    self.formErrors = ko.observableArray();

    self.headers = [
        {title:'Apellido',sortKey:'last_name'},
        {title:'Nombre',sortKey:'first_name'},
        {title:'# Grupo',sortKey:'group'}
    ];

    self.changeFormErrorsVisible = function(visibility) {
        self.formErrorsVisible(visibility);
    };

    self.course = {
        name: ko.observable(),
        id: ko.observable()
    };


    self.type_scales = {
        name: ko.observable(),
        id: ko.observable(),
        description: ko.observable()
    };

    self.model_criteria = {
        scale: ko.observable(),
        criteria:ko.observableArray([])
    };
    self.model_criteria_initials = {
        scale: ko.observable(),
        criteria:ko.observableArray([])
    };

    self.chosen_scale = ko.observable("");
    self.model_criteria.scale.subscribe(function () {
        let val = self.model_criteria ? self.model_criteria.scale() : null;
        self.chosen_scale(val ? self.select.type_scales.filter(d=>d.id === val)[0].description : "");

    });

    self.criteria = ko.observableArray(ko.utils.arrayMap([""], function(item) {
            return { name: ko.observable(item),description: ko.observable(item), id:ko.observable() };
        }));
    self.removeCriterion = function(child) {
            if (self.model_criteria.criteria().length <= 1) {
                vm.formErrors.removeAll();
                vm.changeFormErrorsVisible(true);
                vm.formErrors.push("Debes tener al menos un criterio");
                $('html,body').animate({
                scrollTop: $("#top-form").offset().top},
                'slow');
            }else {
             self.model_criteria.criteria.remove(child);
            }
        };
    self.addCriterion = function () {
            self.model_criteria.criteria.push({ name: ko.observable(""),description: ko.observable(""), editable: ko.observable(true) });
        };

    self.homeworkInitialData = {
        course: ko.observable(),
        description: ko.observable(),
        date_evaluation: ko.observable(),
        date_upload: ko.observable(),
        revision: ko.observable(),
        title: ko.observable(),
        video: ko.observable(),
        homework_to_evaluate: ko.observable()
    };

    self.homework = {
        course: ko.observable(),
        description: ko.observable(),
        date_evaluation: ko.observable(),
        date_upload: ko.observable(),
        revision: ko.observable(),
        title: ko.observable(),
        video: ko.observable(),
        homework_to_evaluate: ko.observable()
    };

    self.checkFormErrors = function() {
        var errors = false;
        self.formErrors.removeAll();
        if (!self.homework.title()) {
            errors = true;
            self.formErrors.push("Debes ingresar título a la tarea");
        }
        if (!self.homework.description()) {
            errors = true;
            self.formErrors.push("Debes ingresar descripción a la tarea");
        }
        if (!self.homework.date_upload()) {
            errors = true;
            self.formErrors.push("Debes ingresar fecha de subida");
        }
        if (!self.homework.date_evaluation()) {
            errors = true;
            self.formErrors.push("Debes ingresar fecha de evaluación");
        } else {
            if (!self.greaterThan(self.homework.date_evaluation(), self.homework.date_upload())) {
                errors = true;
                self.formErrors.push("La fecha de evaluación debe ser posterior a la fecha de subida");
            }
        }
        if(!self.model_criteria.scale()){
               errors = true;
                self.formErrors.push("Debes seleccionar una escale de evaluación");
        }
        for(let c of self.model_criteria.criteria()){
            if(!c.name() || c.name().length < 4){
                errors = true;
                self.formErrors.push("Criterios no válidos");
                break;
            }
        }
        return errors;
    };

    self.discardChangesHomework = function() {
        self.editHomeworkBool(false);
        self.homework.course(self.homeworkInitialData.course());
        self.homework.description(self.homeworkInitialData.description());
        self.homework.date_evaluation(self.homeworkInitialData.date_evaluation());
        self.homework.date_upload(self.homeworkInitialData.date_upload());
        self.homework.revision(self.homeworkInitialData.revision());
        self.homework.title(self.homeworkInitialData.title());
        self.homework.video(self.homeworkInitialData.video());
        self.homework.homework_to_evaluate(self.homeworkInitialData.homework_to_evaluate());
    };

    self.editHomework = function() {
        self.editHomeworkBool(true);
    };

    self.greaterThan = function(value, target) {
        var isValue = value !== undefined && value !== false;
        var isTarget = target !== undefined && target !== false;
        if (isValue && isTarget) {
            return value > target;
        }
        return false;
    };

    self.submitEditHomework = function() {
        var fd = new FormData();
        var mustSubmit = false;
        var hasErrors = self.checkFormErrors();
        if (!hasErrors) {
            if (self.homework.title().localeCompare(self.homeworkInitialData.title()) !== 0) {
                mustSubmit = true;
            }
            fd.append("title", self.homework.title());
            if (self.homework.description().localeCompare(self.homeworkInitialData.description()) !== 0) {
                mustSubmit = true;
            }
            fd.append("description", self.homework.description());
            if (parseInt(self.homework.course()) !== parseInt(self.homeworkInitialData.course())) {
                mustSubmit = true;
            }
            fd.append("course", parseInt(self.homework.course()));
            if (parseInt(self.homework.revision()) !== parseInt(self.homeworkInitialData.revision())) {
                mustSubmit = true;
            }
            fd.append("revision", parseInt(self.homework.revision()));
            if (self.homework.title().localeCompare(self.homeworkInitialData.title()) !== 0) {
                mustSubmit = true;
            }
            fd.append("title", self.homework.title());
            if (self.homework.video()) {
                if (self.homework.video().localeCompare(self.homeworkInitialData.video()) !== 0) {
                    mustSubmit = true;
                }
                fd.append("video", self.homework.video());
            } else {
                if (self.homeworkInitialData.video()) {
                    mustSubmit = true;
                    fd.append("video", "empty");
                }
            }
            if(self.homework.homework_to_evaluate() !== self.homeworkInitialData.homework_to_evaluate()) {
                mustSubmit = true;
                if(self.homework.homework_to_evaluate())
                    fd.append("homework_to_evaluate", self.homework.homework_to_evaluate());
                else
                    fd.append('homework_to_evaluate',self.id());
            }

            //criteria
            fd.append("scale", self.model_criteria.scale());
            if(self.model_criteria.scale !== self.model_criteria_initials.scale()){
                mustSubmit = true;
            }
            let editable_criteria = self.model_criteria.criteria().filter(d=>d.editable);
            let original_criteria = self.model_criteria_initials.criteria().filter(d=>d.editable);
            let results_criteria = [];
            for(let c of editable_criteria){
                if(c.id && c.id()){
                    let original = original_criteria.filter(d=>d.id && d.id() === c.id())[0];
                    if(c.name() !== original.name() || c.description() !== original.description()){
                        results_criteria.push({id:c.id(),name:c.name(),description:c.description(),editable:c.editable()});
                    }
                }else {
                    //new result!
                    results_criteria.push({name:c.name(),description:c.description(),editable:c.editable()})
                }
            }

            if(editable_criteria.filter(d=>d.id).length !== original_criteria.filter(d=>d.id).length){
                //must delete some criteria!
                for(let o of original_criteria.filter(d=>d.id && d.id())){
                    if(editable_criteria.filter(d=>d.id() === o.id()).length === 0){
                        //Deleted element :(
                        results_criteria.push({id:o.id(),name:o.name(),description:o.description(),editable:o.editable(),deleted:true});
                    }
                }
            }

            if(results_criteria.length > 0){
                mustSubmit = true;
                fd.append("criteria", JSON.stringify(results_criteria));
            }

            //end criteria
            fd.append("date_upload", self.homework.date_upload());
            if (self.homework.date_upload().localeCompare(self.homeworkInitialData.date_upload()) !== 0) {
                mustSubmit = true;
            }

            fd.append("date_evaluation", self.homework.date_evaluation());
            if (self.homework.date_evaluation().localeCompare(self.homeworkInitialData.date_evaluation()) !== 0) {
                mustSubmit = true;
            }
            if (mustSubmit) {
                $.ajaxSetup({
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrftoken);
                        }
                    }
                });
                return $.ajax("/teacher/homework/" + self.id() + "/", {
                    data: fd,
                    type: "post",
                    processData: false,
                    contentType: false,
                    success: function(response){
                        $("#editar-group-form-submit").click();
                    }
                });
            } else {
                $("#editar-group-form-submit").click();
            }
        } else {
            self.changeFormErrorsVisible(true);
            $('html,body').animate({
                scrollTop: $("#top-form").offset().top},
                'slow');
        }
    };

    self.submitForms = function() {
        if (self.editGroup.validateGrupos()) {
            if ($("#groups-form").valid() && $("#edit-homework-form").valid()) {
                $("#edit-homework-form-submit").click();
            }
        } else {
            alert("Los números de los grupos no son consecutivos. Revisa si hay algún error.");
        }
    };

    self.submitGroupsForm = function() {
        self.editGroup.currentHomework(self.id());
        var grupos = {};
        for (var i = 0; i < self.editGroup.students().length; i++) {
            student = self.editGroup.students()[i];
            try {
                grupos[student.group().toString()].push(student.id());
            } catch(err) {
                grupos[student.group().toString()] = [student.id()];
            }
        }
        $.when(self.editGroup.submitGroups(grupos, "/teacher/edit-group-form/")).done(
            function (result) {
                if (result.success) {
                    alert("Tarea editada correctamente.");
                    window.location = '/teacher/';
                } else {
                    alert(result.message);
                }
            }
        );
    };
}

var vm = new ViewModel();
