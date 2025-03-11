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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Message, Room
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@require_POST
@csrf_exempt
def upload_file(request, room_id):
    """Handle file uploads for chat messages"""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'error': 'Not authenticated'}, status=401)

    # Get room and file info
    room = get_object_or_404(Room, id=room_id)
    message_text = request.POST.get('message', '')
    file = request.FILES.get('file')

    if not file:
        return JsonResponse({'status': 'error', 'error': 'No file provided'}, status=400)

    try:
        # Check if user is a participant in the room
        if request.user not in room.participants.all():
            return JsonResponse({'status': 'error', 'error': 'Not a participant in this room'}, status=403)

        # Validate file type and size
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 
            'video/mp4', 'video/quicktime', 
            'application/pdf', 'text/plain',
            'audio/webm', 'audio/mpeg', 'audio/ogg'
        ]
        max_file_size = 50 * 1024 * 1024  # 50 MB

        if file.content_type not in allowed_types:
            return JsonResponse({'status': 'error', 'error': 'File type not allowed'}, status=400)

        if file.size > max_file_size:
            return JsonResponse({'status': 'error', 'error': 'File size exceeds limit (50 MB)'}, status=400)

        # Determine message type based on file type
        if file.content_type.startswith('image'):
            message_type = 'image'
        elif file.content_type.startswith('video'):
            message_type = 'video'
        elif file.content_type.startswith('audio'):
            message_type = 'audio'
        elif file.content_type == 'application/pdf':
            message_type = 'file'
        elif file.content_type == 'text/plain':
            message_type = 'file'
        else:
            message_type = 'file'

        # Create message with file
        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=message_text,
            message_type=message_type,
            file=file
        )

        # Get file URL for the response
        file_url = message.file.url if message.file else None

        # Broadcast message to channel group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type': 'chat_message',
                'message': message.content,
                'message_type': message.message_type,
                'username': message.sender.username,
                'user_id': message.sender.id,
                'timestamp': message.timestamp.isoformat(),
                'file_url': file_url
            }
        )

        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'file_url': file_url
        })

    except Room.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Update the user's first name, last name, and username
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.username = request.POST.get('username', user.username)
            user.save()
            form.save()
            return redirect('profile')
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
    
    # Get profile pictures of other participants
    participant_profiles = []
    for participant in other_participants:
        profile = Profile.objects.filter(user=participant).first()
        participant_profiles.append({
            'username': participant.username,
            'profile_picture': profile.profile_picture if profile and profile.profile_picture else None
        })
    
    return render(request, 'chat/room.html', {
        'room': room,
        'room_name': room.name if room.name else ", ".join([user.username for user in other_participants]),
        'messages': messages,
        'other_participants': other_participants,
        'participant_profiles': participant_profiles,
    })

@login_required
def contacts(request):
    user_contacts = Contact.objects.filter(user=request.user).select_related('contact')
    
    # Get IDs of users that are already contacts
    contact_user_ids = [contact.contact.id for contact in user_contacts]
    
    # Add user's own ID to exclude list
    exclude_ids = contact_user_ids + [request.user.id]
    
    # Get up to 10 suggested users that are not already contacts
    suggested_users = User.objects.exclude(
        id__in=exclude_ids
    ).select_related('profile').order_by('?')[:10]  # Random order, limit to 10
    
    form = ContactSearchForm(request.GET)
    search_query = ''
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search', '')
        if search_query:
            # Search for users that are not already contacts
            search_results = User.objects.filter(
                Q(username__icontains=search_query) | 
                Q(email__icontains=search_query)
            ).exclude(
                id__in=exclude_ids
            ).select_related('profile')
            
            return render(request, 'chat/contacts.html', {
                'contacts': user_contacts,
                'search_results': search_results,
                'suggested_users': suggested_users,
                'form': form,
            })
    
    return render(request, 'chat/contacts.html', {
        'contacts': user_contacts,
        'suggested_users': suggested_users,
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
