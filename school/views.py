from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Sequence
from django.contrib import messages
from notifications.services import notify_parents_sequence_published

@login_required
@role_required(['admin'])
def admin_publish_sequence(request):
    sequences = Sequence.objects.all().select_related('term__academic_year').order_by('-term__academic_year__start_date', 'term', 'name')
    
    if request.method == 'POST':
        sequence_id = request.POST.get('sequence')
        action = request.POST.get('action')
        
        if sequence_id:
            sequence = get_object_or_404(Sequence, id=sequence_id)
            if action == 'publish':
                sequence.is_published = True
                sequence.save()
                messages.success(request, f"{sequence} has been published successfully. Marks are now locked and visible to students/parents.")
                # Trigger email notification
                notify_parents_sequence_published(sequence)
            elif action == 'unpublish':
                sequence.is_published = False
                sequence.save()
                messages.warning(request, f"{sequence} has been unpublished. Marks are now hidden and can be edited.")
                
            return redirect('school:publish_sequence')
            
    return render(request, 'school/publish_sequence.html', {
        'sequences': sequences
    })
