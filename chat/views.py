from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse , HttpRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Contact, Room, Message
from .forms import CustomUserCreationForm, ContactSearchForm
from django.shortcuts import get_object_or_404, redirect
from .forms import ProfileForm
from .models import Profile

from django.shortcuts import render, redirect
from .models import Profile
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    # Try to get the profile for the logged-in user, create it if it doesn't exist
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile page after saving the form
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'chat/profile.html', {'form': form})


def delete_chat(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    return redirect('index') 

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def index(request):
    # Get all rooms the user participates in
    rooms = Room.objects.filter(participants=request.user).order_by('-created_at')
    
    # For each room, get the latest message and other participants
    room_data = []
    for room in rooms:
        latest_message = room.messages.last()
        other_participants = room.participants.exclude(id=request.user.id)
        
        # Get profile images of other participants
        participant_profiles = []
        for participant in other_participants:
            profile = Profile.objects.filter(user=participant).first()
            participant_profiles.append({
                'username': participant.username,
                'profile_picture': profile.profile_picture if profile and profile.profile_picture else None
            })
        
        room_info = {
            'id': room.id,
            'name': room.name if room.name else ", ".join([user.username for user in other_participants]),
            'latest_message': latest_message,
            'other_participants': other_participants,
            'participant_profiles': participant_profiles,
            'unread_count': room.messages.filter(is_read=False).exclude(sender=request.user).count(),
        }
        room_data.append(room_info)
    
    return render(request, 'chat/index.html', {
        'room_data': room_data,
    })  

@login_required
def room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Verify user is a participant in the room
    if request.user not in room.participants.all():
        return redirect('index')
    
    # Mark all messages as read
    room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # Get all messages in the room
    messages = room.messages.all()
    
    # Get other participants
    other_participants = room.participants.exclude(id=request.user.id)
    
    return render(request, 'chat/room.html', {
        'room': room,
        'room_name': room.name if room.name else ", ".join([user.username for user in other_participants]),
        'messages': messages,
        'other_participants': other_participants,
    })

@login_required
def contacts(request):
    user_contacts = Contact.objects.filter(user=request.user).select_related('contact')
    
    form = ContactSearchForm(request.GET)
    search_query = ''
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search', '')
        if search_query:
            # Search for users that are not already contacts
            users = User.objects.filter(
                Q(username__icontains=search_query) | 
                Q(email__icontains=search_query)
            ).exclude(
                id__in=[contact.contact.id for contact in user_contacts]
            ).exclude(
                id=request.user.id
            )
            return render(request, 'chat/contacts.html', {
                'contacts': user_contacts,
                'search_results': users,
                'form': form,
            })
    
    return render(request, 'chat/contacts.html', {
        'contacts': user_contacts,
        'form': form,
    })

@login_required
def add_contact(request, user_id):
    contact_user = get_object_or_404(User, id=user_id)
    
    # Can't add yourself as a contact
    if contact_user == request.user:
        return redirect('contacts')
    
    # Check if already a contact
    contact, created = Contact.objects.get_or_create(
        user=request.user,
        contact=contact_user
    )
    
    return redirect('contacts')

@login_required
def remove_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    contact.delete()
    return redirect('contacts')

@login_required
def start_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if a direct chat room already exists between these users
    rooms = Room.objects.filter(
        participants=request.user, 
        is_direct=True
    ).filter(
        participants=other_user
    )
    
    if rooms.exists() and rooms.first().participants.count() == 2:
        # Room exists, redirect to it
        return redirect('room', room_id=rooms.first().id)
    else:
        # Create new room and add both users as participants
        room = Room.objects.create(is_direct=True)
        room.participants.add(request.user, other_user)
        room.save()
        
        return redirect('room', room_id=room.id)

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        selected_contacts = request.POST.getlist('contacts')
        
        if name and selected_contacts:
            # Create new group room
            room = Room.objects.create(
                name=name,
                is_direct=False
            )
            
            # Add current user and selected contacts as participants
            room.participants.add(request.user)
            
            for contact_id in selected_contacts:
                contact = get_object_or_404(Contact, id=contact_id, user=request.user)
                room.participants.add(contact.contact)
            
            room.save()
            
            return redirect('room', room_id=room.id)
    
    # If not POST or invalid data, redirect to contacts page
    return redirect('contacts')

@csrf_exempt
@login_required
def upload_file(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, id=room_id)
        
        # Verify user is a participant in the room
        if request.user not in room.participants.all():
            return JsonResponse({'error': 'You are not a participant in this room'}, status=403)
        
        # Handle file upload
        if 'file' in request.FILES:
            file = request.FILES['file']
            message_type = 'audio' if file.content_type.startswith('audio/') else 'file'
            
            # Create message with file
            message = Message.objects.create(
                room=room,
                sender=request.user,
                file=file,
                message_type=message_type
            )
            
            return JsonResponse({
                'file_url': message.file.url,
                'message_id': message.id
            })
            
    return JsonResponse({'error': 'Invalid request'}, status=400)