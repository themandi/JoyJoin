var container = document.getElementById('quill');
var options = {
    debug: 'info',
    modules: {
    toolbar: [
        [{ header: [1, 2, false] }],
        ['bold', 'italic', 'code-block'],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        ['link', 'image', 'video'],
    ]
    },
    placeholder: 'Skomponuj swój post tutaj',
    theme: 'snow',
};
var editor = new Quill(container, options);

function submit() {
    var contents = editor.getContents();
    var form = document.forms['hidden_form'];

    form.post.value = JSON.stringify(editor.root.innerHTML);
    form.section.value = document.getElementById('section_select').value;
    form.tags.value = document.getElementById('tag_input').value;
    form.title.value = document.getElementById('preview_post_title').textContent

    form.submit();
}
