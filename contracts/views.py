from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from util.security.auth_tools import is_admin_provider, is_admin_required

from .models import Contract
from .forms import ContractForm
from orders.models import Customer


class ListContracts(View):
    template_name = "contracts/contract_list.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_provider)
    def get(self, request, is_admin):

        contracts = Contract.objects.all()

        paginator = Paginator(contracts, 9)
        page_number = request.GET.get("page", 1)
        page_contracts = paginator.get_page(page_number)

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "page_contracts": page_contracts,
            "primary_title": "Contracts",
        })


# Display contract details
class DetailContract(View):
    template_name = "contracts/contract_detail.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_provider)
    def get(self, request, contract_id, is_admin):
        contract = get_object_or_404(Contract, id=contract_id)

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "contract": contract,
            "primary_title": f"{contract}",
        })


class CreateContract(View):
    template_name = "contracts/contract_form.html"

    def get_context_data(self):
        customers = Customer.objects.all()

        return {
            "primary_title": "Create Contract",
            "action": "create",
            "form": ContractForm(),
            "customers": customers,
        }

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = ContractForm(request.POST)

        if form.is_valid():
            new_contract = form.save()
            return redirect('contracts:detail-contract', contract_id=new_contract.id)

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class EditContract(View):
    template_name = "contracts/contract_form.html"

    def get_context_data(self, contract):
        customers = Customer.objects.all()

        return {
            "primary_title": "Edit Contract",
            "action": "update",
            "form": ContractForm(instance=contract),
            "customers": customers,
            "contract": contract,
        }

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, contract_id, *args, **kwargs):
        contract = get_object_or_404(Contract, id=contract_id)
        context = self.get_context_data(contract)
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, contract_id, *args, **kwargs):
        contract = get_object_or_404(Contract, id=contract_id)
        form = ContractForm(request.POST, instance=contract)

        if form.is_valid():
            form.save()
            return redirect('contracts:detail-contract', contract_id=contract.id)

        context = self.get_context_data(contract)
        context['form'] = form
        return render(request, self.template_name, context)


class DeleteContract(View):
    template_name = "contracts/contract_confirm_delete.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, contract_id):
        contract = get_object_or_404(Contract, id=contract_id)
        context = {
            "primary_title": f"Delete Contract {contract}",
            "contract": contract,
        }
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, contract_id):
        contract = get_object_or_404(Contract, id=contract_id)
        contract.delete()
        return redirect('contracts:list-contracts')
