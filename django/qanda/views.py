from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView

from qanda.forms import QuestionForm
from qanda.models import Question

class AskQuestionView(LoginRequiredMixin, CreateView):
    form_class = QuestionForm
    template_name = 'qanda/ask.html'

    def get_initial(self):
        return {
            'user': self.request.user.id
        }

    def form_valid(self, form):
        action = self.request.POST.get('action')
        console.log(action)
        if action == ' SAVE':
            #save the redirect as usual.
            return super().form_valid(form)
        elif action == 'PREVIEW':
            preview = Question(
                question=form.cleaned_data['question'],
                title=form.cleaned_data['title']
            )
            ctx = self.get_context_data(preview=preview)
            return self.render_to_response(context=ctxt)
        return HttpResponseBadRequest()
