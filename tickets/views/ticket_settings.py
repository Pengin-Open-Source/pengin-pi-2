# Ticket Settings is for Staff to decide what options
# they want for Ticket assignment.


class TicketSettings(LoginAndValidationRequiredMixin, UserPassesTestMixin, View):
    template_name = "ticket_owner_list_settings.html"

    def get(self, request):
        context = {}

        show_all_users = self.request.session.get(
            'owner_displays_all_validated_users')
        if show_all_users:
            initial_value = 1
        else:
            initial_value = 0
        form = TicketSettingsForm(
            initial={'show_all_users': initial_value})

        context["form"] = form
        context["primary_title"] = "Ticket Settings"
        return render(request, self.template_name, context)

    def post(self, request):
        form = TicketSettingsForm(request.POST)
        if form.is_valid():
            form_value = int(form.cleaned_data['show_all_users'])
            if form_value:  # 1, Truthy
                show_all_users = True
            else:  # 0, Falsy
                show_all_users = False

            self.request.session['owner_displays_all_validated_users'] = show_all_users

            return redirect('tickets')

        context = {}
        context["form"] = form
        context["primary_title"] = "Ticket Settings"
        return render(request, self.template_name, context)

    def test_func(self):
        if self.request.user.is_staff:
            return True
