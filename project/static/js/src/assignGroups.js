/*
 *  ViewModels for assigning grupos to students
 */

function Student(id, last_name, first_name, group) {
    const self = this;
    self.last_name = ko.observable(last_name);
    self.first_name = ko.observable(first_name);
    self.group = ko.observable(group);
    self.id = ko.observable(id);
}

function AssignGroups() {
    const self = this;
    self.hasCourse = ko.observable(false);
    self.students = ko.observableArray();
    self.studentsByGroup = ko.observable(1);
    self.currentStudent = ko.observable();
    self.currentHomework = ko.observable();

    self.headers = [
        {title: 'Apellido', sortKey: 'last_name'},
        {title: 'Nombre', sortKey: 'first_name'},
        {title: '# Grupo', sortKey: 'group'}
    ];

    self.newListOfGroups = function () {
        const groups = [];
        let j = 0;
        let currentGroup = 1;
        const size = parseInt(self.studentsByGroup());
        for (let i = 0; i < self.students().length; i++) {
            if (j < size) {
                groups.push(currentGroup);
                j++;
            } else {
                currentGroup++;
                groups.push(currentGroup);
                j = 1;
            }
        }
        return groups;
    };

    self.assignRandom = function () {
        const groups = self.newListOfGroups();
        for (i = 0; i < self.students().length; i++) {
            var ri = Math.floor(Math.random() * groups.length);
            const group = groups.splice(ri, 1);
            self.students()[i].group(group);
        }
    };

    self.ifAllHasGroups = function () {
        for (var i = 0; i < self.students().length; i++) {
            var student = self.students()[i];
            if (student.group() === undefined || !student.group()) {
                return false;
            }
        }
        return true;
    };

    self.sortTable = function (sortKey) {
        switch (sortKey) {
            case 'first_name':
                self.students.sort(function (a, b) {
                    return a.first_name() < b.first_name() ? -1 : a.first_name() > b.first_name() ? 1 : a.first_name() === b.first_name() ? 0 : 0;
                });
                break;
            case 'last_name':
                self.students.sort(function (a, b) {
                    return a.last_name() < b.last_name() ? -1 : a.last_name() > b.last_name() ? 1 : a.last_name() === b.last_name() ? 0 : 0;
                });
                break;
            case 'group':
                self.students.sort(function (a, b) {
                    return a.group() < b.group() ? -1 : a.group() > b.group() ? 1 : a.group() === b.group() ? 0 : 0;
                });
                break;
        }
    };

    self.sort = function (header, event) {
        self.sortTable(header.sortKey);
    };

    self.submitGroups = function (groups, url) {
        var fd = new FormData();
        fd.append("groups", JSON.stringify(groups));
        fd.append("homework", parseInt(self.currentHomework()));
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
        return $.ajax(url, {
            data: fd,
            type: "post",
            processData: false,
            contentType: false
        });
    };
}