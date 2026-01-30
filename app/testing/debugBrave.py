import asyncio
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType, DBusError

async def test_brave():
    print("Connecting to DBus...")
    bus = await MessageBus().connect()
    print("✓ Connected\n")
    
    print("=" * 70)
    print("Checking what's actually available on Brave's MPRIS object...")
    print("=" * 70)
    
    try:
        # Try to get Introspectable interface
        print("\n[1] Calling Introspect method...")
        msg = Message(
            destination='org.mpris.MediaPlayer2.brave.instance2',
            path='/org/mpris/MediaPlayer2',
            interface='org.freedesktop.DBus.Introspectable',
            member='Introspect'
        )
        reply = await bus.call(msg)
        introspection_xml = reply.body[0] if reply.body else ""
        print(f"✓ Introspection XML:\n{introspection_xml}\n")
        
    except Exception as e:
        print(f"✗ Error calling Introspect: {e}\n")
    
    try:
        # Try GetAll on Properties interface
        print("[2] Calling Properties.GetAll...")
        msg = Message(
            destination='org.mpris.MediaPlayer2.brave.instance2',
            path='/org/mpris/MediaPlayer2',
            interface='org.freedesktop.DBus.Properties',
            member='GetAll',
            signature='s',
            body=['org.mpris.MediaPlayer2.Player']
        )
        reply = await bus.call(msg)
        properties = reply.body[0] if reply.body else {}
        print(f"✓ Properties:\n{properties}\n")
        
    except Exception as e:
        print(f"✗ Error calling GetAll: {e}\n")
    
    try:
        # Try MediaKeys interface (some players use this)
        print("[3] Calling Properties.GetAll for MediaKeys...")
        msg = Message(
            destination='org.mpris.MediaPlayer2.brave.instance2',
            path='/org/mpris/MediaPlayer2',
            interface='org.freedesktop.DBus.Properties',
            member='GetAll',
            signature='s',
            body=['org.mpris.MediaPlayer2']
        )
        reply = await bus.call(msg)
        properties = reply.body[0] if reply.body else {}
        print(f"✓ Properties:\n{properties}\n")
        
    except Exception as e:
        print(f"✗ Error calling GetAll for root: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_brave())
