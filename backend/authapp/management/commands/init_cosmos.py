from django.core.management.base import BaseCommand
from aiCore.cosmos_service import cosmos_service

class Command(BaseCommand):
    help = 'Initialize Cosmos DB database and all containers'

    def handle(self, *args, **options):
        self.stdout.write('Initializing Cosmos DB...')
        
        try:
            # Create database if it doesn't exist
            cosmos_service.create_database_if_not_exists()
            self.stdout.write(self.style.SUCCESS('Database created/verified successfully'))
            
            # Create all containers if they don't exist
            self.stdout.write('Creating containers...')
            cosmos_service.create_all_containers()
            self.stdout.write(self.style.SUCCESS('All containers created/verified successfully'))
            
            # Display container statistics
            self.stdout.write('Container Statistics:')
            stats = cosmos_service.get_container_stats()
            for container_type, stat in stats.items():
                if 'error' in stat:
                    self.stdout.write(
                        self.style.WARNING(f'  {container_type}: {stat["error"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'  {container_type}: {stat["id"]} (Partition Key: {stat["partition_key"]["paths"][0]})')
                    )
            
            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('Cosmos DB Initialization Complete!'))
            self.stdout.write('='*50)
            self.stdout.write(f'Database: {cosmos_service.database.id}')
            self.stdout.write(f'Containers: {len(cosmos_service.containers)}')
            self.stdout.write('='*50)
            self.stdout.write(self.style.SUCCESS('Ready for Cosmos DB only operations!'))
            self.stdout.write('='*50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing Cosmos DB: {e}')
            )
